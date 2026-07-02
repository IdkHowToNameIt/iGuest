"""Shared FastAPI dependencies."""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Host
from app.services.auth import AuthError, decode_token

# auto_error=False so we can return a uniform 401 with our own message
_bearer = HTTPBearer(auto_error=False)


def _decode_or_401(credentials: HTTPAuthorizationCredentials | None) -> dict:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return decode_token(credentials.credentials)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """Protect a route: require a valid admin bearer token.

    Returns the admin subject (username) on success; raises 401 otherwise.
    Host tokens (``role == "host"``) are explicitly rejected here.
    """
    payload = _decode_or_401(credentials)
    if payload.get("role") == "host":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return payload.get("sub", "")


def require_host(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Host:
    """Protect a host route: require a valid host token and load the Host.

    Raises 401 for an invalid token or 403 if the host no longer exists or was
    deactivated.
    """
    payload = _decode_or_401(credentials)
    if payload.get("role") != "host":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Host access required.",
        )
    try:
        host_id = uuid.UUID(payload.get("sub", ""))
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")

    host = db.get(Host, host_id)
    if host is None or not host.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Host account is not available.",
        )
    return host
