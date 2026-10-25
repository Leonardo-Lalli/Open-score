"""Teacher accounts and signed sessions for the school LAN deployment.

Every write requires a teacher session. Students and anonymous visitors keep
read-only access. A session is a signed cookie carrying the teacher id and
email; the server never trusts the client for the role or the ownership.
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

COOKIE_NAME = 'open_score_session'
DEFAULT_TTL = 12 * 60 * 60
FAILURE_WINDOW = 300.0
MAX_FAILURES = 5
LOCKOUT_SECONDS = 60.0
PBKDF2_ITERATIONS = 260_000
MIN_PASSWORD_LENGTH = 8


def _truthy(value: str | None) -> bool:
    return str(value or '').strip().lower() in ('1', 'true', 'yes', 'on')


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode('ascii').rstrip('=')


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + '=' * (-len(value) % 4))


def load_or_create_secret(path: Path) -> bytes:
    """Read the signing secret, creating a random one on first use."""
    try:
        existing = path.read_text(encoding='utf-8').strip()
    except FileNotFoundError:
        existing = ''
    if len(existing) >= 32:
        return existing.encode('utf-8')
    path.parent.mkdir(parents=True, exist_ok=True)
    value = secrets.token_urlsafe(48)
    path.write_text(value, encoding='utf-8')
    try:
        os.chmod(path, 0o600)
    except OSError:
        # Windows has no POSIX mode bits; the data directory stays local.
        pass
    return value.encode('utf-8')


def normalize_email(email: str | None) -> str:
    return str(email or '').strip().casefold()


def hash_password(password: str) -> str:
    if len(password or '') < MIN_PASSWORD_LENGTH:
        raise ValueError(f'La password deve contenere almeno {MIN_PASSWORD_LENGTH} caratteri')
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt,
                                 PBKDF2_ITERATIONS)
    return f'pbkdf2_sha256${PBKDF2_ITERATIONS}${_b64encode(salt)}${_b64encode(digest)}'


def verify_password(password: str | None, encoded: str | None) -> bool:
    if password is None or not encoded:
        return False
    try:
        algorithm, iterations, salt_text, digest_text = encoded.split('$', 3)
        if algorithm != 'pbkdf2_sha256':
            return False
        salt = _b64decode(salt_text)
        expected = _b64decode(digest_text)
        actual = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt,
                                     int(iterations))
    except (AttributeError, ValueError):
        return False
    return hmac.compare_digest(actual, expected)


def _row_dict(row) -> dict | None:
    if row is None:
        return None
    if hasattr(row, 'keys'):
        return dict(row)
    return dict(zip(('id', 'email', 'password_hash', 'display_name', 'created_at'), row))


def create_teacher(db, email: str, password: str, display_name: str = '') -> int:
    email = normalize_email(email)
    if '@' not in email or len(email) < 3:
        raise ValueError('Email non valida')
    password_hash = hash_password(password)
    try:
        cursor = db.execute(
            'INSERT INTO teachers(email,password_hash,display_name) VALUES (?,?,?)',
            (email, password_hash, (display_name or '').strip()),
        )
    except sqlite3.IntegrityError as exc:
        raise ValueError('Email già registrata') from exc
    return cursor.lastrowid


def ensure_teacher(db, email: str, password: str, display_name: str = '') -> int:
    """Create the bootstrap teacher if absent; never overwrite its password."""
    email = normalize_email(email)
    row = db.execute('SELECT id FROM teachers WHERE email=?', (email,)).fetchone()
    if row is not None:
        return row['id'] if hasattr(row, 'keys') else row[0]
    return create_teacher(db, email, password, display_name)


def find_teacher(db, email: str) -> dict | None:
    email = normalize_email(email)
    row = db.execute('SELECT * FROM teachers WHERE email=?', (email,)).fetchone()
    return _row_dict(row)


def authenticate(db, email: str, password: str | None) -> dict | None:
    teacher = find_teacher(db, email)
    if teacher is None or not verify_password(password, teacher['password_hash']):
        return None
    return {key: teacher[key] for key in ('id', 'email', 'display_name', 'created_at')}


def list_teachers(db) -> list[dict]:
    result = []
    for row in db.execute(
            'SELECT id,email,display_name,created_at FROM teachers ORDER BY email'):
        item = _row_dict(row)
        if item is not None:
            result.append(item)
    return result


def set_password(db, email: str, password: str) -> int:
    teacher = find_teacher(db, email)
    if teacher is None:
        raise ValueError('Docente non trovato')
    db.execute('UPDATE teachers SET password_hash=? WHERE id=?',
               (hash_password(password), teacher['id']))
    return teacher['id']


@dataclass
class Auth:
    secret: bytes = b''
    ttl: int = DEFAULT_TTL
    cookie_secure: bool = False
    failures: dict[str, list[float]] = field(default_factory=dict)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def issue(self, teacher_id: int, email: str, now: float | None = None) -> str:
        expires = int((now if now is not None else time.time()) + self.ttl)
        payload = json.dumps({'exp': expires, 'tid': int(teacher_id),
                              'email': normalize_email(email)},
                             separators=(',', ':'), ensure_ascii=False).encode('utf-8')
        body = _b64encode(payload)
        signature = hmac.new(self.secret, body.encode('ascii'),
                             hashlib.sha256).hexdigest()
        return f'{body}.{signature}'

    def decode(self, token: str | None, now: float | None = None) -> dict | None:
        if not token:
            return None
        try:
            body, signature = token.split('.', 1)
            expected = hmac.new(self.secret, body.encode('ascii'),
                                hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected):
                return None
            data = json.loads(_b64decode(body).decode('utf-8'))
            expires = int(data['exp'])
            if expires < int(now if now is not None else time.time()):
                return None
            teacher_id = int(data['tid'])
            email = str(data['email'])
        except (AttributeError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            return None
        if not teacher_id or not email:
            return None
        return {'teacher_id': teacher_id, 'email': email, 'expires': expires}

    def valid(self, token: str | None, now: float | None = None) -> bool:
        return self.decode(token, now) is not None

    def session_from_request(self, request) -> dict | None:
        return self.decode(request.cookies.get(COOKIE_NAME))

    def login_allowed(self, key: str, now: float | None = None) -> bool:
        now = now if now is not None else time.time()
        with self.lock:
            attempts = [stamp for stamp in self.failures.get(key, [])
                        if now - stamp < FAILURE_WINDOW]
            self.failures[key] = attempts
            if len(attempts) < MAX_FAILURES:
                return True
            return now - attempts[-1] >= LOCKOUT_SECONDS

    def record_failure(self, key: str, now: float | None = None) -> None:
        now = now if now is not None else time.time()
        with self.lock:
            attempts = [stamp for stamp in self.failures.get(key, [])
                        if now - stamp < FAILURE_WINDOW]
            attempts.append(now)
            self.failures[key] = attempts

    def record_success(self, key: str) -> None:
        with self.lock:
            self.failures.pop(key, None)


def build(base_dir: Path, secret: str | bytes | None = None,
          cookie_secure: bool | None = None) -> Auth:
    """Create the session configuration, reading the environment as a fallback."""
    if secret is not None:
        secret_bytes = secret.encode('utf-8') if isinstance(secret, str) else secret
    else:
        env_secret = os.environ.get('TORNEO_SECRET', '').strip()
        secret_bytes = (env_secret.encode('utf-8') if env_secret
                        else load_or_create_secret(base_dir / 'data' / 'session.secret'))

    try:
        hours = float(os.environ.get('TORNEO_SESSION_HOURS', '12'))
    except ValueError:
        hours = 12.0
    ttl = max(1, int(hours * 3600))

    if cookie_secure is None:
        cookie_secure = _truthy(os.environ.get('TORNEO_COOKIE_SECURE'))

    return Auth(secret=secret_bytes, ttl=ttl, cookie_secure=cookie_secure)
