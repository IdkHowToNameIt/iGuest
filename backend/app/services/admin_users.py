"""
Extra administrator accounts, alongside the legacy .env admin.

The original single admin (ADMIN_USERNAME/ADMIN_PASSWORD, see
app/services/auth.py) keeps working unchanged — it's the fallback login that
can never be locked out. This module authenticates the additional DB-backed
accounts an admin can create from the panel, following the same pattern as
host accounts (bcrypt password hash, temporary password issued at creation).
"""

import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AdminUser
from app.services.passwords import _to_bytes, verify_password

# Same constant-time-ish padding trick as host_auth._DUMMY_HASH: spend
# roughly the same time verifying an unknown username as a known one.
_DUMMY_HASH = bcrypt.hashpw(b"dummy-password", bcrypt.gensalt())


class AdminUserAuthError(Exception):
    """Raised when admin-user credentials are invalid or the account is disabled."""


def authenticate_admin_user(db: Session, username: str, password: str) -> AdminUser:
    """Return the active AdminUser matching the credentials, or raise AdminUserAuthError."""
    user = db.execute(select(AdminUser).where(AdminUser.username == username)).scalars().first()
    if user is None or not user.is_active:
        bcrypt.checkpw(_to_bytes(password), _DUMMY_HASH)
        raise AdminUserAuthError("Invalid credentials.")
    if not verify_password(password, user.password_hash):
        raise AdminUserAuthError("Invalid credentials.")
    return user
