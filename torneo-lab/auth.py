"""Single-organiser authentication for the school LAN deployment.

With no password and no API token configured the app stays in local demo mode:
writes remain open, exactly as in earlier phases. Setting
``TORNEO_ADMIN_PASSWORD`` (or ``TORNEO_API_TOKEN``) turns every state-changing
``/api`` call into an admin-only operation. Reads and ``/public`` stay open, so
spectators never need credentials.
"""

import hashlib
import hmac
import os
import secrets
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

COOKIE_NAME = 'open_score_session'
DEFAULT_TTL = 12 * 60 * 60
FAILURE_WINDOW = 300.0
MAX_FAILURES = 5
LOCKOUT_SECONDS = 60.0


def _truthy(value: str | None) -> bool:
    return str(value or '').strip().lower() in ('1', 'true', 'yes', 'on')


def load_or_create_secret(path: Path) -> bytes:
    """Read the signing secret, creating a random one on first use.

    The file is excluded from Git with the rest of ``data/``. It must survive
    restarts, otherwise every session is invalidated.
    """
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


@dataclass
class Auth:
    password: str | None = None
    api_token: str | None = None
    secret: bytes = b''
    ttl: int = DEFAULT_TTL
    cookie_secure: bool = False
    failures: dict[str, list[float]] = field(default_factory=dict)
    lock: threading.Lock = field(default_factory=threading.Lock)

    @property
    def required(self) -> bool:
        return bool(self.password or self.api_token)

    def issue(self, now: float | None = None) -> str:
        expires = int((now if now is not None else time.time()) + self.ttl)
        nonce = secrets.token_urlsafe(12)
        payload = f'{expires}.{nonce}'
        signature = hmac.new(self.secret, payload.encode('utf-8'),
                             hashlib.sha256).hexdigest()
        return f'{payload}.{signature}'

    def valid(self, token: str | None, now: float | None = None) -> bool:
        if not token:
            return False
        try:
            expires_text, nonce, signature = token.split('.', 2)
            expires = int(expires_text)
        except (AttributeError, ValueError):
            return False
        payload = f'{expires_text}.{nonce}'
        expected = hmac.new(self.secret, payload.encode('utf-8'),
                            hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return False
        return expires >= int(now if now is not None else time.time())

    def check_password(self, candidate: str | None) -> bool:
        if not self.password or candidate is None:
            return False
        return hmac.compare_digest(candidate.encode('utf-8'),
                                   self.password.encode('utf-8'))

    def check_api_token(self, candidate: str | None) -> bool:
        if not self.api_token or not candidate:
            return False
        return hmac.compare_digest(candidate.encode('utf-8'),
                                   self.api_token.encode('utf-8'))

    def is_authenticated(self, request) -> bool:
        if self.valid(request.cookies.get(COOKIE_NAME)):
            return True
        header = request.headers.get('authorization', '')
        if header.lower().startswith('bearer '):
            return self.check_api_token(header[7:].strip())
        return False

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


def build(base_dir: Path, password: str | None = None,
          api_token: str | None = None, secret: str | bytes | None = None,
          cookie_secure: bool | None = None) -> Auth:
    """Create the auth configuration, reading the environment as a fallback."""
    resolved_password = (password if password is not None
                         else os.environ.get('TORNEO_ADMIN_PASSWORD', '')).strip() or None
    resolved_token = (api_token if api_token is not None
                      else os.environ.get('TORNEO_API_TOKEN', '')).strip() or None

    if secret is not None:
        secret_bytes = secret.encode('utf-8') if isinstance(secret, str) else secret
    elif resolved_password or resolved_token:
        env_secret = os.environ.get('TORNEO_SECRET', '').strip()
        secret_bytes = (env_secret.encode('utf-8') if env_secret
                        else load_or_create_secret(base_dir / 'data' / 'session.secret'))
    else:
        # No authentication: keep an ephemeral secret, never touch the disk.
        secret_bytes = secrets.token_bytes(32)

    try:
        hours = float(os.environ.get('TORNEO_SESSION_HOURS', '12'))
    except ValueError:
        hours = 12.0
    ttl = max(1, int(hours * 3600))

    if cookie_secure is None:
        cookie_secure = _truthy(os.environ.get('TORNEO_COOKIE_SECURE'))

    return Auth(password=resolved_password, api_token=resolved_token,
                secret=secret_bytes, ttl=ttl, cookie_secure=cookie_secure)
