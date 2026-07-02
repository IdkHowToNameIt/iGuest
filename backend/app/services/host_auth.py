"""
Host authentication.

Hosts are created by the admin and scoped to a single unit. Passwords are
stored as bcrypt hashes (see ``app.services.passwords``); login verifies the
password and issues a JWT carrying ``role="host"`` plus the host id and unit
id, reusing the same signing secret/expiry as the admin token (see
``services.auth``).
"""

import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Host
from app.services.auth import create_access_token
from app.services.passwords import _to_bytes, hash_password, verify_password

# A fixed bcrypt hash (of an arbitrary password) used by ``authenticate_host`` to
# spend roughly the same time verifying when the email is unknown, masking the
# "no such host" vs "wrong password" timing difference. Computed once at import.
_DUMMY_HASH = bcrypt.hashpw(b"dummy-password", bcrypt.gensalt())


class HostAuthError(Exception):
    """Raised when host credentials are invalid or the account is disabled."""


def authenticate_host(db: Session, email: str, password: str) -> Host:
    """Return the active Host matching the credentials, or raise HostAuthError."""
    host = db.execute(select(Host).where(Host.email == email)).scalars().first()
    # Verify against a constant dummy hash when the host is missing to reduce
    # the timing signal that distinguishes "unknown email" from "wrong password".
    if host is None or not host.is_active:
        bcrypt.checkpw(_to_bytes(password), _DUMMY_HASH)
        raise HostAuthError("Invalid credentials.")
    if not verify_password(password, host.password_hash):
        raise HostAuthError("Invalid credentials.")
    return host


def create_host_token(host: Host) -> str:
    return create_access_token(
        sub=str(host.id),
        role="host",
        extra={"structure_id": str(host.structure_id)},
    )
