"""Server sessions, password hashing and authorization. No bearer privileges in QR URLs."""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from db import database

COOKIE = "open_score_platform_session"
ITERATIONS = 600_000


def now():
    return datetime.now(timezone.utc)


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def fail(status, code, message, **extra):
    raise HTTPException(status, dict(code=code, message=message, **extra))


def password_hash(password):
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), ITERATIONS
    )
    return f"pbkdf2_sha256${ITERATIONS}${salt}${hashed.hex()}"


def verify_password(password, stored):
    try:
        algorithm, iterations, salt, expected = stored.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        if len(salt) != 32 or len(expected) != 64:
            from auth import verify_password as legacy_verify

            return legacy_verify(password, stored)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt), int(iterations)
        )
        return hmac.compare_digest(actual.hex(), expected)
    except (ValueError, TypeError):
        return False


def create_teacher(
    db, email, password, display_name, organization_name=None, organization_id=None
):
    """Administrative CLI only; public registration cannot select this role."""
    from v1_schemas import RegisterInput

    data = RegisterInput(email=email, password=password, display_name=display_name)
    if db.execute("SELECT 1 FROM users WHERE email=?", (data.email,)).fetchone():
        raise ValueError("Account già esistente")
    if organization_id is not None:
        if not db.execute(
            "SELECT 1 FROM organizations WHERE id=?", (organization_id,)
        ).fetchone():
            raise ValueError("Contesto non trovato")
        oid = organization_id
    else:
        if not organization_name or not 1 <= len(organization_name.strip()) <= 120:
            raise ValueError("Nome contesto richiesto, 1–120 caratteri")
        oid = db.execute(
            "INSERT INTO organizations(name) VALUES (?)", (organization_name.strip(),)
        ).lastrowid
    uid = db.execute(
        "INSERT INTO users(email,display_name,password_hash,role,organization_id) VALUES (?,?,?,?,?)",
        (data.email, data.display_name, password_hash(password), "teacher", oid),
    ).lastrowid
    from identity_bridge import ensure_legacy_teacher

    ensure_legacy_teacher(
        db, dict(db.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone())
    )
    return uid


def public_user(user):
    return {k: user[k] for k in ("id", "display_name", "role", "organization_id")}


def session(db, request, required=True):
    raw = request.cookies.get(COOKIE, "")
    record = (
        db.execute(
            "SELECT * FROM sessions WHERE token_hash=? AND expires_at>?",
            (digest(raw), now().isoformat()),
        ).fetchone()
        if raw
        else None
    )
    if required and (not record or record["user_id"] is None):
        fail(401, "authentication_required", "Accedi per continuare")
    if record and record["user_id"] is not None:
        disabled = db.execute(
            "SELECT 1 FROM teachers t JOIN teacher_user_links l ON l.teacher_id=t.id WHERE l.user_id=? AND t.active=0",
            (record["user_id"],),
        ).fetchone()
        if disabled:
            fail(401, "account_disabled", "Account disattivato")
    return dict(record) if record else None


def csrf(request, record):
    token = request.headers.get("X-CSRF-Token", "")
    if not record or not hmac.compare_digest(token, record["csrf_token"]):
        fail(403, "csrf_invalid", "Token CSRF mancante o scaduto")


def new_session(db, response, secure, user_id=None, old=None):
    if old:
        db.execute("DELETE FROM sessions WHERE token_hash=?", (old["token_hash"],))
    raw, token = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    seconds = 8 * 3600 if user_id else 1800
    db.execute("DELETE FROM sessions WHERE expires_at<=?", (now().isoformat(),))
    db.execute(
        "INSERT INTO sessions VALUES (?,?,?,?)",
        (digest(raw), user_id, token, (now() + timedelta(seconds=seconds)).isoformat()),
    )
    response.set_cookie(
        COOKIE,
        raw,
        max_age=seconds,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )
    return token


def rate_limit(path, request, label, maximum=20):
    # Store hashes, not plaintext IP addresses or emails; failures still commit.
    key = digest(f"{label}|{request.client.host if request.client else 'unknown'}")
    denied = False
    with database(path, True) as db:
        stamp = now()
        db.execute(
            "DELETE FROM auth_attempts WHERE expires_at<=?", (stamp.isoformat(),)
        )
        item = db.execute(
            "SELECT attempts FROM auth_attempts WHERE key=?", (key,)
        ).fetchone()
        if item and item["attempts"] >= maximum:
            denied = True
        elif item:
            db.execute(
                "UPDATE auth_attempts SET attempts=attempts+1 WHERE key=?", (key,)
            )
        else:
            db.execute(
                "INSERT INTO auth_attempts VALUES (?,1,?)",
                (key, (stamp + timedelta(minutes=15)).isoformat()),
            )
    if denied:
        fail(429, "rate_limited", "Troppi tentativi; riprova più tardi")


def teacher(user):
    if user["role"] != "teacher":
        fail(403, "teacher_required", "Operazione riservata al professore")


def manages(db, user, tournament):
    return user["role"] == "teacher" and (
        tournament["owner_id"] == user["id"]
        or (
            tournament["organization_id"] == user["organization_id"]
            and db.execute(
                "SELECT 1 FROM tournament_collaborators WHERE tournament_id=? AND user_id=?",
                (tournament["id"], user["id"]),
            ).fetchone()
            is not None
        )
    )


def require_active(tournament):
    if tournament.get("archived_at"):
        fail(409, "tournament_archived", "Ripristinare il torneo prima di modificarlo")


def access(db, user, tid, write=False):
    record = db.execute("SELECT * FROM tournaments WHERE id=?", (tid,)).fetchone()
    if not record:
        fail(404, "not_found", "Torneo non trovato")
    tournament = dict(record)
    manager = manages(db, user, tournament)
    enrolled = db.execute(
        "SELECT 1 FROM students WHERE tournament_id=? AND user_id=?", (tid, user["id"])
    ).fetchone()
    if not manager and not enrolled:
        fail(404, "not_found", "Torneo non trovato")
    if write:
        require_active(tournament)
    if write and not manager:
        fail(403, "teacher_required", "Operazione riservata al professore")
    return tournament


def version(record, expected, column="version"):
    if record[column] != expected:
        fail(
            409,
            "stale_version",
            "Dati cambiati: rileggi la risorsa",
            current_version=record[column],
        )
