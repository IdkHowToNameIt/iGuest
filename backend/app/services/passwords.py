"""Generic bcrypt password hashing helpers, shared by host and admin-user auth."""

import secrets

import bcrypt


def _to_bytes(password: str) -> bytes:
    """Encode a password for bcrypt, truncating to its 72-byte input limit.

    bcrypt only considers the first 72 bytes and (since v4.1) raises on longer
    input, so we truncate explicitly rather than reject over-long passwords.
    """
    return password.encode("utf-8")[:72]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_to_bytes(password), bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(_to_bytes(password), password_hash.encode("ascii"))


def generate_temp_password(length: int = 12) -> str:
    """A readable URL-safe temporary password handed to a newly created account."""
    return secrets.token_urlsafe(length)[:length]
