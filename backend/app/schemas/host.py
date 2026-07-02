"""Request/response schemas for the host-facing API."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ── auth ──────────────────────────────────────────────────────────────────────

class HostLoginRequest(BaseModel):
    email: str
    password: str


class HostTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    # Signals the frontend to force the change-password flow before anything else.
    must_change_password: bool


class HostChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


# ── profile ─────────────────────────────────────────────────────────────────────

class HostUnitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str


class HostMeOut(BaseModel):
    id: uuid.UUID
    email: str
    must_change_password: bool
    structure_id: uuid.UUID
    structure_name: str
    units: list[HostUnitOut]
    avatar_url: str | None = None


# ── documents (read-only) ───────────────────────────────────────────────────────

class HostDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scope_type: str
    # Which unit a unit-scoped document belongs to (null for shared/structure docs).
    unit_id: uuid.UUID | None = None
    original_filename: str
    file_type: str
    status: str
    created_at: datetime


class HostDocumentContentOut(BaseModel):
    """A document's extracted plain text, for the host's in-app text viewer."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    file_type: str
    status: str
    extracted_text: str | None
    error_message: str | None = None


# ── FAQ ─────────────────────────────────────────────────────────────────────────

class FaqEntryOut(BaseModel):
    rank: int
    question: str
    answer: str
    answer_language: str | None = None


# ── document change requests ─────────────────────────────────────────────────────

class ChangeRequestCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=4000)
    # Tie the request to a specific document, OR leave document_id null and provide
    # a `title` for an "other" problem (the two are mutually exclusive).
    document_id: uuid.UUID | None = None
    title: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def _document_or_title(self) -> "ChangeRequestCreate":
        if self.document_id is None and not (self.title and self.title.strip()):
            raise ValueError("Provide a document_id, or a title for an 'other' request.")
        if self.document_id is not None:
            self.title = None  # a document-scoped request never carries a title
        return self


class ChangeRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    structure_id: uuid.UUID
    document_id: uuid.UUID | None
    title: str | None
    body: str
    status: str
    admin_note: str | None
    resolved_at: datetime | None
    created_at: datetime
    # Display name of the (single) admin account, joined in for the host's
    # notes view so it doesn't just read "Admin". Falls back to "Admin" when
    # the admin has not set a display name.
    admin_name: str | None = None
