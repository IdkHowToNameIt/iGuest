"""
Capability-link management for guest access.

A GuestLink is a capability URL: whoever holds the long random token can chat
about that unit, no login required. We never expose sequential IDs and the
token is generated with the cryptographic `secrets` module.

The validity check is a pure function (`check_link_validity`) so the
valid / revoked / expired / not-yet-valid logic can be unit-tested without a DB.
"""

import secrets
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import GuestLink
from app.models.base import utcnow

# 32 bytes → ~43 url-safe chars: 256 bits of entropy, not brute-forceable.
TOKEN_NBYTES = 32


# ── errors ───────────────────────────────────────────────────────────────────

class LinkError(Exception):
    """Base class for link resolution errors. `code` is machine-readable."""

    code = "link_error"


class LinkNotFoundError(LinkError):
    code = "not_found"


class LinkRevokedError(LinkError):
    code = "revoked"


class LinkExpiredError(LinkError):
    code = "expired"


class LinkNotYetValidError(LinkError):
    code = "not_yet_valid"


# ── token generation ───────────────────────────────────────────────────────────

def generate_token() -> str:
    """Return a new long, URL-safe, cryptographically random token."""
    return secrets.token_urlsafe(TOKEN_NBYTES)


# ── validity (pure) ─────────────────────────────────────────────────────────────

def check_link_validity(link: GuestLink, now: datetime | None = None) -> None:
    """Raise a LinkError subclass if *link* cannot currently be used.

    Reads only `status`, `valid_from`, `valid_until` so it can be tested with a
    lightweight stand-in object. Returns None when the link is usable.
    """
    now = now or utcnow()

    if link.status == "revoked":
        raise LinkRevokedError("This link has been revoked.")

    if link.valid_from is not None and now < link.valid_from:
        raise LinkNotYetValidError("This link is not active yet.")

    if link.valid_until is not None and now > link.valid_until:
        raise LinkExpiredError("This link has expired.")


# ── persistence ─────────────────────────────────────────────────────────────────

def create_guest_link(
    db: Session,
    unit_id: uuid.UUID,
    valid_from: datetime | None = None,
    valid_until: datetime | None = None,
) -> GuestLink:
    """Create and persist a new active GuestLink for *unit_id*."""
    link = GuestLink(
        unit_id=unit_id,
        token=generate_token(),
        status="active",
        valid_from=valid_from,
        valid_until=valid_until,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def get_link_by_token(db: Session, token: str) -> GuestLink | None:
    """Look up a GuestLink by its token, or None."""
    stmt = select(GuestLink).where(GuestLink.token == token)
    return db.execute(stmt).scalar_one_or_none()


def resolve_link(db: Session, token: str, now: datetime | None = None) -> GuestLink:
    """Resolve *token* to a usable GuestLink.

    Raises:
        LinkNotFoundError: token does not exist.
        LinkRevokedError / LinkExpiredError / LinkNotYetValidError: not usable.
    """
    link = get_link_by_token(db, token)
    if link is None:
        raise LinkNotFoundError("Unknown link token.")
    check_link_validity(link, now)
    return link


def delete_link(db: Session, link: GuestLink) -> None:
    """Delete a guest link entirely (revocation = deletion).

    The link row and its conversations/messages are removed (cascade), so the
    token stops working (resolves to "not found") and the link no longer appears
    anywhere in the admin UI.
    """
    db.delete(link)
    db.commit()
