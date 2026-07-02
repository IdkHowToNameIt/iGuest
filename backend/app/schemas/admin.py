"""Request/response schemas for the admin API."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ── auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    # Signals the frontend to force the change-password flow before anything
    # else. Always False for the legacy .env account (see app.services.auth).
    must_change_password: bool = False


class AdminChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


# ── admin profile (single account) ─────────────────────────────────────────────

class AdminProfileOut(BaseModel):
    display_name: str | None = None
    avatar_url: str | None = None
    updated_at: datetime


class AdminProfileUpdate(BaseModel):
    display_name: str | None = Field(None, max_length=200)


# ── dashboard stats ─────────────────────────────────────────────────────────────

class AdminStatsOut(BaseModel):
    structures: int
    units: int
    active_links: int
    open_change_requests: int


# ── structure ───────────────────────────────────────────────────────────────────

class StructureCreate(BaseModel):
    name: str = Field(..., min_length=1)
    country_language: str = Field(..., min_length=2, description="BCP-47 code, e.g. 'it'")
    owner_contact: str = Field(..., min_length=1)
    # Location (validated client-side against /api/geo) and admin-only contacts.
    region: str | None = None
    province: str | None = None
    city: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    welcome_message: str | None = Field(None, max_length=2000)


class StructureUpdate(BaseModel):
    name: str | None = Field(None, min_length=1)
    country_language: str | None = Field(None, min_length=2)
    owner_contact: str | None = Field(None, min_length=1)
    region: str | None = None
    province: str | None = None
    city: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    welcome_message: str | None = Field(None, max_length=2000)


class StructureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    country_language: str
    owner_contact: str
    region: str | None = None
    province: str | None = None
    city: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    welcome_message: str | None = None
    created_at: datetime


# ── unit ────────────────────────────────────────────────────────────────────────

class UnitCreate(BaseModel):
    name: str = Field(..., min_length=1)
    owner_contact: str | None = None


class UnitUpdate(BaseModel):
    name: str | None = Field(None, min_length=1)
    owner_contact: str | None = None


class UnitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    structure_id: uuid.UUID
    name: str
    owner_contact: str | None
    created_at: datetime


# ── document ─────────────────────────────────────────────────────────────────────

class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scope_type: str
    structure_id: uuid.UUID
    unit_id: uuid.UUID | None
    original_filename: str
    file_type: str
    status: str
    error_message: str | None
    created_at: datetime


class DocumentContentOut(BaseModel):
    """A document's extracted plain text, for the in-app text viewer."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    file_type: str
    status: str
    extracted_text: str | None
    error_message: str | None = None


# ── guest link ───────────────────────────────────────────────────────────────────

class GuestLinkCreate(BaseModel):
    valid_from: datetime | None = None
    valid_until: datetime | None = None


class GuestLinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    unit_id: uuid.UUID
    token: str
    status: str
    valid_from: datetime | None
    valid_until: datetime | None
    created_at: datetime


# ── conversations ─────────────────────────────────────────────────────────────────

class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: str
    content: str
    detected_language: str | None
    created_at: datetime


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    guest_link_id: uuid.UUID
    unit_id: uuid.UUID
    created_at: datetime
    delete_after: datetime | None


class ConversationDetailOut(ConversationOut):
    messages: list[MessageOut]


# ── hosts ──────────────────────────────────────────────────────────────────────

class HostCreate(BaseModel):
    email: str = Field(..., min_length=3, description="Host login email")


class HostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    structure_id: uuid.UUID
    email: str
    must_change_password: bool
    is_active: bool
    created_at: datetime


class HostCreatedOut(HostOut):
    # The temporary password is returned exactly once, at creation or reset.
    # Null on an update that did not reset the password.
    temp_password: str | None = None


class HostUpdate(BaseModel):
    is_active: bool | None = None
    # When true, a new temporary password is generated and returned.
    reset_password: bool = False


# ── admin accounts (additional logins, alongside the legacy .env admin) ───────────

class AdminUserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    must_change_password: bool
    is_active: bool
    created_at: datetime


class AdminUserCreatedOut(AdminUserOut):
    # The temporary password is returned exactly once, at creation or reset.
    # Null on an update that did not reset the password.
    temp_password: str | None = None


class AdminUserUpdate(BaseModel):
    is_active: bool | None = None
    # When true, a new temporary password is generated and returned.
    reset_password: bool = False


# ── document change requests ───────────────────────────────────────────────────

class ChangeRequestAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    structure_id: uuid.UUID
    host_id: uuid.UUID | None
    document_id: uuid.UUID | None
    title: str | None
    body: str
    status: str
    admin_note: str | None
    resolved_at: datetime | None
    created_at: datetime
    # Context joined in for the inbox view
    structure_name: str | None = None
    host_email: str | None = None


class ChangeRequestUpdate(BaseModel):
    status: str = Field(..., pattern="^(open|resolved)$")
    admin_note: str | None = None


# ── analytics ──────────────────────────────────────────────────────────────────

class AnalyticsQuestionOut(BaseModel):
    question: str
    count: int
    share: float


class AnalyticsCategoryOut(BaseModel):
    label: str
    count: int
    share: float
    questions: list[AnalyticsQuestionOut]


class AnalyticsOut(BaseModel):
    total: int
    categories: list[AnalyticsCategoryOut]

    @classmethod
    def from_unit_analytics(cls, analytics) -> "AnalyticsOut":
        """Map a ``faq.analytics.UnitAnalytics`` dataclass to the response model."""
        return cls(
            total=analytics.total,
            categories=[
                AnalyticsCategoryOut(
                    label=c.label,
                    count=c.count,
                    share=c.share,
                    questions=[
                        AnalyticsQuestionOut(question=q.question, count=q.count, share=q.share)
                        for q in c.questions
                    ],
                )
                for c in analytics.categories
            ],
        )
