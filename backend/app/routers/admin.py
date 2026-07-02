"""
Admin API (single administrator).

  POST /api/admin/login                         → obtain a bearer token (unprotected)

  All routes below require a valid admin bearer token:

  Structures:   POST/GET/GET{id}/PATCH{id}/DELETE{id}  /api/admin/structures
  Units:        POST/GET   /api/admin/structures/{sid}/units
                GET/PATCH/DELETE  /api/admin/units/{id}
  Documents:    POST /api/admin/documents (multipart, scope chosen via form)
                GET  /api/admin/documents  (optional structure_id / unit_id filters)
                GET  /api/admin/documents/{id}/content   (extracted text)
                DELETE /api/admin/documents/{id}
  Links:        POST/GET /api/admin/units/{uid}/links
                POST /api/admin/links/{id}/revoke
  Conversations:GET /api/admin/units/{uid}/conversations
                GET /api/admin/conversations/{id}
                DELETE /api/admin/conversations/{id}   (GDPR)
  Structures:   GET /api/admin/structures supports q / region / province / city filters
  Hosts:        POST/GET /api/admin/structures/{sid}/hosts
                PATCH/DELETE /api/admin/hosts/{id}     (deactivate / reset password)
  Admin accts:  POST/GET /api/admin/admins             (additional admin logins)
                PATCH/DELETE /api/admin/admins/{id}    (deactivate / reset password)
                POST /api/admin/change-password        (self-service, DB-backed admins only)
  Change reqs:  GET /api/admin/change-requests  (optional status / structure_id filters)
                PATCH /api/admin/change-requests/{id}  (resolve + admin note)
  Visit reqs:   GET /api/admin/visit-requests   (landing leads; optional status filter)
                PATCH/DELETE /api/admin/visit-requests/{id}  (contact/archive/note or drop)
  Analytics:    GET /api/admin/analytics            (question categories, all properties)
                GET /api/admin/units/{uid}/analytics
  Profile:      GET/PATCH /api/admin/profile   (display name for the single admin account)
                POST/DELETE /api/admin/profile/avatar
  Stats:        GET /api/admin/stats           (dashboard overview counts)
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import require_admin
from app.models import (
    AdminProfile,
    AdminUser,
    Conversation,
    Document,
    DocumentChangeRequest,
    GuestLink,
    Host,
    Message,
    Structure,
    Unit,
    VisitRequest,
)
from app.models.base import utcnow
from app.schemas.admin import (
    AdminChangePasswordRequest,
    AdminProfileOut,
    AdminProfileUpdate,
    AdminStatsOut,
    AdminUserCreate,
    AdminUserCreatedOut,
    AdminUserOut,
    AdminUserUpdate,
    AnalyticsOut,
    ChangeRequestAdminOut,
    ChangeRequestUpdate,
    ConversationDetailOut,
    ConversationOut,
    DocumentContentOut,
    DocumentOut,
    GuestLinkCreate,
    GuestLinkOut,
    HostCreate,
    HostCreatedOut,
    HostOut,
    HostUpdate,
    LoginRequest,
    MessageOut,
    StructureCreate,
    StructureOut,
    StructureUpdate,
    TokenResponse,
    UnitCreate,
    UnitOut,
    UnitUpdate,
    VisitRequestAdminOut,
    VisitRequestUpdate,
)
from app.services.admin_documents import create_and_ingest_document
from app.services.auth import AuthError, authenticate_admin, create_access_token
from app.services.avatars import AvatarError, MAX_UPLOAD_BYTES, delete_avatar_file, save_avatar
from app.services.faq import build_global_analytics, build_unit_analytics
from app.services.links import create_guest_link, delete_link
from app.services.passwords import generate_temp_password, hash_password, verify_password
from app.services.uploads import UploadTooLargeError, read_upload_limited

# ── login (unprotected) ────────────────────────────────────────────────────────

login_router = APIRouter(prefix="/api/admin", tags=["admin-auth"])


@login_router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    try:
        sub, must_change_password = authenticate_admin(db, body.username, body.password)
    except AuthError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials."
        )
    return TokenResponse(
        access_token=create_access_token(sub=sub), must_change_password=must_change_password
    )


# ── protected router ─────────────────────────────────────────────────────────────

router = APIRouter(
    prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)]
)


def _get_or_404(db: Session, model, obj_id: uuid.UUID, name: str):
    obj = db.get(model, obj_id)
    if obj is None:
        raise HTTPException(status_code=404, detail=f"{name} not found.")
    return obj


# ── structures ──────────────────────────────────────────────────────────────────

@router.post("/structures", response_model=StructureOut, status_code=201)
def create_structure(body: StructureCreate, db: Session = Depends(get_db)):
    structure = Structure(**body.model_dump())
    db.add(structure)
    db.commit()
    db.refresh(structure)
    return structure


@router.get("/structures", response_model=list[StructureOut])
def list_structures(
    q: str | None = None,
    region: str | None = None,
    province: str | None = None,
    city: str | None = None,
    db: Session = Depends(get_db),
):
    """List structures, optionally filtered/searched.

    ``region``/``province``/``city`` are exact (case-insensitive) location
    filters; ``q`` is a free-text search matched against name/city/province/region.
    All provided constraints are AND-ed, so combinations like region+city or
    name+city progressively narrow the results.
    """
    stmt = select(Structure)
    if region:
        stmt = stmt.where(func.lower(Structure.region) == region.lower())
    if province:
        stmt = stmt.where(func.lower(Structure.province) == province.lower())
    if city:
        stmt = stmt.where(func.lower(Structure.city) == city.lower())
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Structure.name.ilike(like),
                Structure.city.ilike(like),
                Structure.province.ilike(like),
                Structure.region.ilike(like),
            )
        )
    return db.execute(stmt.order_by(Structure.created_at)).scalars().all()


@router.get("/structures/{structure_id}", response_model=StructureOut)
def get_structure(structure_id: uuid.UUID, db: Session = Depends(get_db)):
    return _get_or_404(db, Structure, structure_id, "Structure")


@router.patch("/structures/{structure_id}", response_model=StructureOut)
def update_structure(
    structure_id: uuid.UUID, body: StructureUpdate, db: Session = Depends(get_db)
):
    structure = _get_or_404(db, Structure, structure_id, "Structure")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(structure, field, value)
    db.commit()
    db.refresh(structure)
    return structure


@router.delete("/structures/{structure_id}", status_code=204)
def delete_structure(structure_id: uuid.UUID, db: Session = Depends(get_db)):
    structure = _get_or_404(db, Structure, structure_id, "Structure")
    db.delete(structure)
    db.commit()
    return Response(status_code=204)


# ── units ──────────────────────────────────────────────────────────────────────

@router.post("/structures/{structure_id}/units", response_model=UnitOut, status_code=201)
def create_unit(structure_id: uuid.UUID, body: UnitCreate, db: Session = Depends(get_db)):
    _get_or_404(db, Structure, structure_id, "Structure")
    unit = Unit(structure_id=structure_id, **body.model_dump())
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit


@router.get("/structures/{structure_id}/units", response_model=list[UnitOut])
def list_units(structure_id: uuid.UUID, db: Session = Depends(get_db)):
    _get_or_404(db, Structure, structure_id, "Structure")
    stmt = select(Unit).where(Unit.structure_id == structure_id).order_by(Unit.created_at)
    return db.execute(stmt).scalars().all()


@router.get("/units/{unit_id}", response_model=UnitOut)
def get_unit(unit_id: uuid.UUID, db: Session = Depends(get_db)):
    return _get_or_404(db, Unit, unit_id, "Unit")


@router.patch("/units/{unit_id}", response_model=UnitOut)
def update_unit(unit_id: uuid.UUID, body: UnitUpdate, db: Session = Depends(get_db)):
    unit = _get_or_404(db, Unit, unit_id, "Unit")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(unit, field, value)
    db.commit()
    db.refresh(unit)
    return unit


@router.delete("/units/{unit_id}", status_code=204)
def delete_unit(unit_id: uuid.UUID, db: Session = Depends(get_db)):
    unit = _get_or_404(db, Unit, unit_id, "Unit")
    db.delete(unit)
    db.commit()
    return Response(status_code=204)


# ── documents ────────────────────────────────────────────────────────────────────

@router.post("/documents", response_model=DocumentOut, status_code=201)
def upload_document(
    scope_type: str = Form(..., description="'structure' or 'unit'"),
    target_id: uuid.UUID = Form(..., description="structure_id or unit_id per scope"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if scope_type == "unit":
        unit = _get_or_404(db, Unit, target_id, "Unit")
        structure_id, unit_id = unit.structure_id, unit.id
    elif scope_type == "structure":
        structure = _get_or_404(db, Structure, target_id, "Structure")
        structure_id, unit_id = structure.id, None
    else:
        raise HTTPException(status_code=422, detail="scope_type must be 'structure' or 'unit'.")

    try:
        content = read_upload_limited(
            file.file,
            max_bytes=settings.max_document_upload_bytes,
            label="Document",
        )
    except UploadTooLargeError as exc:
        raise HTTPException(status_code=413, detail=str(exc))
    document = create_and_ingest_document(
        db, scope_type, structure_id, unit_id, file.filename, content
    )
    return document


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(
    structure_id: uuid.UUID | None = None,
    unit_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(Document)
    if structure_id is not None:
        stmt = stmt.where(Document.structure_id == structure_id)
    if unit_id is not None:
        stmt = stmt.where(Document.unit_id == unit_id)
    stmt = stmt.order_by(Document.created_at)
    return db.execute(stmt).scalars().all()


@router.get("/documents/{document_id}/content", response_model=DocumentContentOut)
def get_document_content(document_id: uuid.UUID, db: Session = Depends(get_db)):
    """The document's extracted plain text (for the in-app text viewer)."""
    return _get_or_404(db, Document, document_id, "Document")


@router.delete("/documents/{document_id}", status_code=204)
def delete_document(document_id: uuid.UUID, db: Session = Depends(get_db)):
    document = _get_or_404(db, Document, document_id, "Document")
    db.delete(document)  # chunks cascade
    db.commit()
    return Response(status_code=204)


# ── guest links ───────────────────────────────────────────────────────────────────

@router.post("/units/{unit_id}/links", response_model=GuestLinkOut, status_code=201)
def create_link(unit_id: uuid.UUID, body: GuestLinkCreate, db: Session = Depends(get_db)):
    _get_or_404(db, Unit, unit_id, "Unit")
    return create_guest_link(db, unit_id, body.valid_from, body.valid_until)


@router.get("/units/{unit_id}/links", response_model=list[GuestLinkOut])
def list_links(unit_id: uuid.UUID, db: Session = Depends(get_db)):
    _get_or_404(db, Unit, unit_id, "Unit")
    # Revoking a link deletes it (see delete_link), so only "active" rows should
    # ever exist here — filtered defensively in case any legacy "revoked" rows
    # (from before revoke started hard-deleting) are still lying around.
    stmt = (
        select(GuestLink)
        .where(GuestLink.unit_id == unit_id, GuestLink.status == "active")
        .order_by(GuestLink.created_at)
    )
    return db.execute(stmt).scalars().all()


@router.post("/links/{link_id}/revoke", status_code=204)
def revoke_guest_link(link_id: uuid.UUID, db: Session = Depends(get_db)):
    """Revoke a link = delete it (and its chat). It stops working and disappears."""
    link = _get_or_404(db, GuestLink, link_id, "Link")
    delete_link(db, link)
    return Response(status_code=204)


# ── conversations ─────────────────────────────────────────────────────────────────

@router.get("/units/{unit_id}/conversations", response_model=list[ConversationOut])
def list_conversations(unit_id: uuid.UUID, db: Session = Depends(get_db)):
    _get_or_404(db, Unit, unit_id, "Unit")
    stmt = (
        select(Conversation)
        .where(Conversation.unit_id == unit_id)
        .order_by(Conversation.created_at.desc())
    )
    return db.execute(stmt).scalars().all()


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailOut)
def get_conversation(conversation_id: uuid.UUID, db: Session = Depends(get_db)):
    conversation = _get_or_404(db, Conversation, conversation_id, "Conversation")
    messages = (
        db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        .scalars()
        .all()
    )
    return ConversationDetailOut(
        id=conversation.id,
        guest_link_id=conversation.guest_link_id,
        unit_id=conversation.unit_id,
        created_at=conversation.created_at,
        delete_after=conversation.delete_after,
        messages=[MessageOut.model_validate(m) for m in messages],
    )


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: uuid.UUID, db: Session = Depends(get_db)):
    """GDPR: delete a conversation and all its messages (cascade)."""
    conversation = _get_or_404(db, Conversation, conversation_id, "Conversation")
    db.delete(conversation)
    db.commit()
    return Response(status_code=204)


# ── hosts ────────────────────────────────────────────────────────────────────────

@router.post("/structures/{structure_id}/hosts", response_model=HostCreatedOut, status_code=201)
def create_host(structure_id: uuid.UUID, body: HostCreate, db: Session = Depends(get_db)):
    """Create a host for a structure with a temporary password (returned once)."""
    _get_or_404(db, Structure, structure_id, "Structure")
    if db.execute(select(Host).where(Host.email == body.email)).scalars().first():
        raise HTTPException(status_code=409, detail="A host with this email already exists.")
    temp_password = generate_temp_password()
    host = Host(
        structure_id=structure_id,
        email=body.email,
        password_hash=hash_password(temp_password),
        must_change_password=True,
    )
    db.add(host)
    db.commit()
    db.refresh(host)
    out = HostCreatedOut.model_validate(host)
    out.temp_password = temp_password
    return out


@router.get("/structures/{structure_id}/hosts", response_model=list[HostOut])
def list_hosts(structure_id: uuid.UUID, db: Session = Depends(get_db)):
    _get_or_404(db, Structure, structure_id, "Structure")
    stmt = select(Host).where(Host.structure_id == structure_id).order_by(Host.created_at)
    return db.execute(stmt).scalars().all()


@router.patch("/hosts/{host_id}", response_model=HostCreatedOut)
def update_host(host_id: uuid.UUID, body: HostUpdate, db: Session = Depends(get_db)):
    """Toggle ``is_active`` and/or issue a new temporary password.

    The temporary password is present in the response only when ``reset_password``
    was requested; otherwise it is null.
    """
    host = _get_or_404(db, Host, host_id, "Host")
    if body.is_active is not None:
        host.is_active = body.is_active
    temp_password = None
    if body.reset_password:
        temp_password = generate_temp_password()
        host.password_hash = hash_password(temp_password)
        host.must_change_password = True
    db.commit()
    db.refresh(host)
    out = HostCreatedOut.model_validate(host)
    out.temp_password = temp_password
    return out


@router.delete("/hosts/{host_id}", status_code=204)
def delete_host(host_id: uuid.UUID, db: Session = Depends(get_db)):
    host = _get_or_404(db, Host, host_id, "Host")
    db.delete(host)  # change requests keep host_id via ON DELETE SET NULL
    db.commit()
    return Response(status_code=204)


# ── admin accounts (additional logins, alongside the legacy .env admin) ───────────

@router.post("/admins", response_model=AdminUserCreatedOut, status_code=201)
def create_admin_user(body: AdminUserCreate, db: Session = Depends(get_db)):
    """Create an additional admin login with a temporary password (returned once)."""
    if body.username == settings.admin_username:
        raise HTTPException(
            status_code=409, detail="That username is reserved for the built-in admin account."
        )
    if db.execute(select(AdminUser).where(AdminUser.username == body.username)).scalars().first():
        raise HTTPException(status_code=409, detail="An admin account with this username already exists.")
    temp_password = generate_temp_password()
    admin_user = AdminUser(
        username=body.username,
        password_hash=hash_password(temp_password),
        must_change_password=True,
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    out = AdminUserCreatedOut.model_validate(admin_user)
    out.temp_password = temp_password
    return out


@router.get("/admins", response_model=list[AdminUserOut])
def list_admin_users(db: Session = Depends(get_db)):
    stmt = select(AdminUser).order_by(AdminUser.created_at)
    return db.execute(stmt).scalars().all()


@router.patch("/admins/{admin_id}", response_model=AdminUserCreatedOut)
def update_admin_user(
    admin_id: uuid.UUID,
    body: AdminUserUpdate,
    db: Session = Depends(get_db),
    admin_sub: str = Depends(require_admin),
):
    """Toggle ``is_active`` and/or issue a new temporary password.

    The temporary password is present in the response only when ``reset_password``
    was requested; otherwise it is null. An admin cannot disable their own account.
    """
    admin_user = _get_or_404(db, AdminUser, admin_id, "Admin account")
    if body.is_active is False and str(admin_user.id) == admin_sub:
        raise HTTPException(status_code=400, detail="You cannot disable your own account.")
    if body.is_active is not None:
        admin_user.is_active = body.is_active
    temp_password = None
    if body.reset_password:
        temp_password = generate_temp_password()
        admin_user.password_hash = hash_password(temp_password)
        admin_user.must_change_password = True
    db.commit()
    db.refresh(admin_user)
    out = AdminUserCreatedOut.model_validate(admin_user)
    out.temp_password = temp_password
    return out


@router.delete("/admins/{admin_id}", status_code=204)
def delete_admin_user(
    admin_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin_sub: str = Depends(require_admin),
):
    admin_user = _get_or_404(db, AdminUser, admin_id, "Admin account")
    if str(admin_user.id) == admin_sub:
        raise HTTPException(status_code=400, detail="You cannot delete your own account.")
    db.delete(admin_user)
    db.commit()
    return Response(status_code=204)


@router.post("/change-password", status_code=204)
def change_own_password(
    body: AdminChangePasswordRequest,
    db: Session = Depends(get_db),
    admin_sub: str = Depends(require_admin),
):
    """Rotate the caller's own password.

    Only meaningful for DB-backed admin accounts — the legacy .env admin's
    credentials are static configuration, not something an HTTP call can change.
    """
    try:
        admin_uuid = uuid.UUID(admin_sub)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="The built-in admin account's password is set via .env, not here.",
        )
    admin_user = db.get(AdminUser, admin_uuid)
    if admin_user is None:
        raise HTTPException(status_code=404, detail="Admin account not found.")
    if not verify_password(body.current_password, admin_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    admin_user.password_hash = hash_password(body.new_password)
    admin_user.must_change_password = False
    db.commit()
    return None


# ── document change requests (admin inbox) ─────────────────────────────────────────

@router.get("/change-requests", response_model=list[ChangeRequestAdminOut])
def list_change_requests(
    status: str | None = None,
    structure_id: uuid.UUID | None = None,
    type: str | None = None,  # "document" (tied to a doc) or "other" (free-form)
    db: Session = Depends(get_db),
):
    stmt = (
        select(DocumentChangeRequest, Structure.name, Host.email)
        .join(Structure, DocumentChangeRequest.structure_id == Structure.id)
        .outerjoin(Host, DocumentChangeRequest.host_id == Host.id)
        .order_by(DocumentChangeRequest.created_at.desc())
    )
    if status is not None:
        stmt = stmt.where(DocumentChangeRequest.status == status)
    if structure_id is not None:
        stmt = stmt.where(DocumentChangeRequest.structure_id == structure_id)
    # Type is derived from whether the request references a document.
    if type == "document":
        stmt = stmt.where(DocumentChangeRequest.document_id.is_not(None))
    elif type == "other":
        stmt = stmt.where(DocumentChangeRequest.document_id.is_(None))

    out: list[ChangeRequestAdminOut] = []
    for req, structure_name, host_email in db.execute(stmt).all():
        item = ChangeRequestAdminOut.model_validate(req)
        item.structure_name = structure_name
        item.host_email = host_email
        out.append(item)
    return out


@router.patch("/change-requests/{request_id}", response_model=ChangeRequestAdminOut)
def update_change_request(
    request_id: uuid.UUID, body: ChangeRequestUpdate, db: Session = Depends(get_db)
):
    req = _get_or_404(db, DocumentChangeRequest, request_id, "Change request")
    req.status = body.status
    if body.admin_note is not None:
        req.admin_note = body.admin_note
    req.resolved_at = datetime.now(timezone.utc) if body.status == "resolved" else None
    db.commit()
    db.refresh(req)
    return ChangeRequestAdminOut.model_validate(req)


# ── visit requests (leads from the public landing) ─────────────────────────────────

@router.get("/visit-requests", response_model=list[VisitRequestAdminOut])
def list_visit_requests(status: str | None = None, db: Session = Depends(get_db)):
    stmt = select(VisitRequest).order_by(VisitRequest.created_at.desc())
    if status is not None:
        stmt = stmt.where(VisitRequest.status == status)
    return db.execute(stmt).scalars().all()


@router.patch("/visit-requests/{request_id}", response_model=VisitRequestAdminOut)
def update_visit_request(
    request_id: uuid.UUID, body: VisitRequestUpdate, db: Session = Depends(get_db)
):
    req = _get_or_404(db, VisitRequest, request_id, "Visit request")
    req.status = body.status
    if body.admin_note is not None:
        req.admin_note = body.admin_note
    # "handled" once it leaves the "new" state (contacted or archived).
    req.handled_at = datetime.now(timezone.utc) if body.status != "new" else None
    db.commit()
    db.refresh(req)
    return VisitRequestAdminOut.model_validate(req)


@router.delete("/visit-requests/{request_id}", status_code=204)
def delete_visit_request(request_id: uuid.UUID, db: Session = Depends(get_db)):
    req = _get_or_404(db, VisitRequest, request_id, "Visit request")
    db.delete(req)
    db.commit()
    return Response(status_code=204)


# ── analytics ──────────────────────────────────────────────────────────────────────

@router.get("/analytics", response_model=AnalyticsOut)
def get_global_analytics(db: Session = Depends(get_db)):
    """Guest questions grouped into topic categories across all properties."""
    return AnalyticsOut.from_unit_analytics(build_global_analytics(db))


@router.get("/units/{unit_id}/analytics", response_model=AnalyticsOut)
def get_unit_analytics(unit_id: uuid.UUID, db: Session = Depends(get_db)):
    _get_or_404(db, Unit, unit_id, "Unit")
    return AnalyticsOut.from_unit_analytics(build_unit_analytics(db, unit_id))


# ── admin profile (single account, no DB-backed login) ────────────────────────────

def _get_or_create_profile(db: Session) -> AdminProfile:
    profile = (
        db.execute(select(AdminProfile).order_by(AdminProfile.created_at)).scalars().first()
    )
    if profile is None:
        # updated_at is set explicitly (rather than relying on the column's
        # insert-time default) so the value is already populated for the
        # response model even before a real flush/refresh round-trip.
        profile = AdminProfile(updated_at=utcnow())
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.get("/profile", response_model=AdminProfileOut)
def get_profile(db: Session = Depends(get_db)):
    profile = _get_or_create_profile(db)
    return AdminProfileOut(
        display_name=profile.display_name,
        avatar_url=profile.avatar_path,
        updated_at=profile.updated_at,
    )


@router.patch("/profile", response_model=AdminProfileOut)
def update_profile(body: AdminProfileUpdate, db: Session = Depends(get_db)):
    profile = _get_or_create_profile(db)
    # Always assign (not `if body.display_name is not None`): the frontend sends
    # null to explicitly clear the name, which is indistinguishable from "leave
    # unchanged" under a not-None guard, so clearing never used to persist.
    profile.display_name = body.display_name
    profile.updated_at = utcnow()
    db.commit()
    db.refresh(profile)
    return AdminProfileOut(
        display_name=profile.display_name,
        avatar_url=profile.avatar_path,
        updated_at=profile.updated_at,
    )


@router.post("/profile/avatar", response_model=AdminProfileOut)
def upload_profile_avatar(file: UploadFile = File(...), db: Session = Depends(get_db)):
    profile = _get_or_create_profile(db)
    try:
        content = read_upload_limited(file.file, max_bytes=MAX_UPLOAD_BYTES, label="Image")
    except UploadTooLargeError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    try:
        new_path = save_avatar(content, file.content_type or "")
    except AvatarError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    delete_avatar_file(profile.avatar_path)
    profile.avatar_path = new_path
    profile.updated_at = utcnow()
    db.commit()
    db.refresh(profile)
    return AdminProfileOut(
        display_name=profile.display_name,
        avatar_url=profile.avatar_path,
        updated_at=profile.updated_at,
    )


@router.delete("/profile/avatar", response_model=AdminProfileOut)
def delete_profile_avatar(db: Session = Depends(get_db)):
    profile = _get_or_create_profile(db)
    delete_avatar_file(profile.avatar_path)
    profile.avatar_path = None
    profile.updated_at = utcnow()
    db.commit()
    db.refresh(profile)
    return AdminProfileOut(
        display_name=profile.display_name,
        avatar_url=profile.avatar_path,
        updated_at=profile.updated_at,
    )


# ── dashboard stats ────────────────────────────────────────────────────────────────

@router.get("/stats", response_model=AdminStatsOut)
def get_stats(db: Session = Depends(get_db)):
    structures = db.execute(select(func.count(Structure.id))).scalar_one()
    units = db.execute(select(func.count(Unit.id))).scalar_one()
    active_links = db.execute(
        select(func.count(GuestLink.id)).where(GuestLink.status == "active")
    ).scalar_one()
    open_change_requests = db.execute(
        select(func.count(DocumentChangeRequest.id)).where(
            DocumentChangeRequest.status == "open"
        )
    ).scalar_one()
    new_visit_requests = db.execute(
        select(func.count(VisitRequest.id)).where(VisitRequest.status == "new")
    ).scalar_one()
    return AdminStatsOut(
        structures=structures,
        units=units,
        active_links=active_links,
        open_change_requests=open_change_requests,
        new_visit_requests=new_visit_requests,
    )
