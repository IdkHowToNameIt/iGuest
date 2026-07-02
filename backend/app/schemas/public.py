"""Request/response schemas for the public (unauthenticated) API.

These back the landing page: anyone can submit a "book a visit" lead without
logging in, so the payload is deliberately small and self-contained.
"""

from datetime import date

from pydantic import BaseModel, Field

# A pragmatic email check (no external email-validator dependency, matching the
# rest of the codebase which stores emails as plain strings).
_EMAIL_RE = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class VisitRequestCreate(BaseModel):
    structure_name: str = Field(..., min_length=1, max_length=200)
    city: str | None = Field(None, max_length=200)
    business_type: str | None = Field(None, max_length=100)
    contact_name: str = Field(..., min_length=1, max_length=200)
    contact_email: str = Field(..., pattern=_EMAIL_RE, max_length=320)
    preferred_date: date | None = None


class VisitRequestCreatedOut(BaseModel):
    """Minimal confirmation returned to the anonymous submitter."""

    ok: bool = True
