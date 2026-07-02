"""
Admin authentication — a legacy single administrator from .env, plus any
additional DB-backed accounts created from the panel (see app.services.admin_users).

Login verifies the .env username/password (constant-time compare) first, and
falls back to the admin_user table. Either way it issues a short-lived JWT.
Protected routes just validate the JWT — nothing afterwards distinguishes the
two kinds of admin account.
"""

import secrets
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.services.admin_users import AdminUserAuthError, authenticate_admin_user

ALGORITHM = "HS256"


class AuthError(Exception):
    """Raised when credentials or a token are invalid/expired."""


def verify_credentials(username: str, password: str) -> bool:
    """Constant-time check of the supplied credentials against .env config."""
    user_ok = secrets.compare_digest(username, settings.admin_username)
    pass_ok = secrets.compare_digest(password, settings.admin_password)
    # Evaluate both sides regardless to avoid early-exit timing differences
    return user_ok and pass_ok


def authenticate_admin(db: Session, username: str, password: str) -> tuple[str, bool]:
    """Verify admin credentials against the .env account or a DB admin_user row.

    Returns ``(jwt_subject, must_change_password)``; raises AuthError if
    neither matches. The .env account is checked first and never requires a
    password change — it's the fallback that keeps working no matter what
    happens to the DB-backed accounts.
    """
    if verify_credentials(username, password):
        return settings.admin_username, False
    try:
        user = authenticate_admin_user(db, username, password)
    except AdminUserAuthError as exc:
        raise AuthError("Invalid credentials.") from exc
    return str(user.id), user.must_change_password


def create_access_token(
    now: datetime | None = None,
    *,
    sub: str | None = None,
    role: str = "admin",
    extra: dict | None = None,
) -> str:
    """Issue a signed JWT, expiring after the configured window.

    Defaults to an admin token. Host tokens pass ``sub`` (the host id),
    ``role="host"`` and ``extra`` claims (e.g. ``unit_id``). The same secret
    and expiry window are reused; the ``role`` claim is what distinguishes the
    two audiences (see ``require_admin`` / ``require_host``).
    """
    now = now or datetime.now(timezone.utc)
    payload = {
        "sub": sub or settings.admin_username,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.admin_token_expire_minutes)).timestamp()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.admin_jwt_secret, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT. Raises AuthError if invalid or expired."""
    try:
        return jwt.decode(token, settings.admin_jwt_secret, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise AuthError("Token has expired.") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthError("Invalid token.") from exc
