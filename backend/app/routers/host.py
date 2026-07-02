"""
Host-facing API.

Hosts are created by the admin and scoped to a single structure. A host can log
in, change their (initially temporary) password, read all of their structure's
documentation (across its units), view the FAQ/analytics, and submit document
change requests to the admin.

  POST /api/host/login                       → obtain a bearer token (unprotected)

  All routes below require a valid host bearer token:

  GET   /api/host/me                          → host profile + structure + units
  POST  /api/host/change-password             → rotate the password
  POST  /api/host/me/avatar                    → upload a profile picture
  DELETE /api/host/me/avatar                   → remove the profile picture
  GET   /api/host/documents                   → structure documents (read-only)
  GET   /api/host/documents/{id}/content      → a document's extracted text
  GET   /api/host/faqs                         → generated FAQ entries (structure)
  GET   /api/host/analytics                    → question analytics (structure, "General")
  GET   /api/host/units/{id}/analytics         → question analytics for one unit
  GET   /api/host/change-requests              → the host's own change requests
  POST  /api/host/change-requests              → submit a change request
"""

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_host
from app.models import Document, DocumentChangeRequest, Host, Structure, Unit
from app.models.admin_profile import AdminProfile
from app.schemas.admin import AnalyticsOut
from app.schemas.host import (
    ChangeRequestCreate,
    ChangeRequestOut,
    FaqEntryOut,
    HostChangePasswordRequest,
    HostDocumentContentOut,
    HostDocumentOut,
    HostLoginRequest,
    HostMeOut,
    HostTokenResponse,
    HostUnitOut,
)
from app.services.avatars import AvatarError, delete_avatar_file, save_avatar
from app.services.faq import build_structure_analytics, build_unit_analytics, list_structure_faqs
from app.services.host_auth import (
    HostAuthError,
    authenticate_host,
    create_host_token,
    hash_password,
    verify_password,
)

# ── login (unprotected) ────────────────────────────────────────────────────────

login_router = APIRouter(prefix="/api/host", tags=["host-auth"])


@login_router.post("/login", response_model=HostTokenResponse)
def login(body: HostLoginRequest, db: Session = Depends(get_db)):
    try:
        host = authenticate_host(db, body.email, body.password)
    except HostAuthError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials."
        )
    return HostTokenResponse(
        access_token=create_host_token(host),
        must_change_password=host.must_change_password,
    )


# ── protected router ─────────────────────────────────────────────────────────────

router = APIRouter(prefix="/api/host", tags=["host"])


def _admin_display_name(db: Session) -> str:
    """The single admin account's display name, or "Admin" if unset."""
    profile = db.execute(select(AdminProfile)).scalars().first()
    return (profile.display_name if profile else None) or "Admin"


def _structure_units(db: Session, structure_id: uuid.UUID) -> list[Unit]:
    return list(
        db.execute(
            select(Unit).where(Unit.structure_id == structure_id).order_by(Unit.created_at)
        )
        .scalars()
        .all()
    )


def _build_me(db: Session, host: Host) -> HostMeOut:
    structure = db.get(Structure, host.structure_id)
    units = _structure_units(db, host.structure_id)
    return HostMeOut(
        id=host.id,
        email=host.email,
        must_change_password=host.must_change_password,
        structure_id=structure.id,
        structure_name=structure.name,
        units=[HostUnitOut.model_validate(u) for u in units],
        avatar_url=host.avatar_path,
    )


@router.get("/me", response_model=HostMeOut)
def get_me(host: Host = Depends(require_host), db: Session = Depends(get_db)):
    return _build_me(db, host)


@router.post("/me/avatar", response_model=HostMeOut)
def upload_avatar(
    file: UploadFile = File(...), host: Host = Depends(require_host), db: Session = Depends(get_db)
):
    content = file.file.read()
    try:
        new_path = save_avatar(content, file.content_type or "")
    except AvatarError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    delete_avatar_file(host.avatar_path)
    host.avatar_path = new_path
    db.commit()
    db.refresh(host)
    return _build_me(db, host)


@router.delete("/me/avatar", response_model=HostMeOut)
def delete_avatar(host: Host = Depends(require_host), db: Session = Depends(get_db)):
    delete_avatar_file(host.avatar_path)
    host.avatar_path = None
    db.commit()
    db.refresh(host)
    return _build_me(db, host)


@router.post("/change-password", status_code=204)
def change_password(
    body: HostChangePasswordRequest,
    host: Host = Depends(require_host),
    db: Session = Depends(get_db),
):
    if not verify_password(body.current_password, host.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    host.password_hash = hash_password(body.new_password)
    host.must_change_password = False
    db.commit()
    return None


@router.get("/documents", response_model=list[HostDocumentOut])
def list_documents(host: Host = Depends(require_host), db: Session = Depends(get_db)):
    """All documents of the host's structure — shared ones plus every unit's own.

    ``Document.structure_id`` is always populated (even for unit-scoped docs), so a
    single filter covers both scopes.
    """
    stmt = (
        select(Document)
        .where(Document.structure_id == host.structure_id)
        .order_by(Document.created_at)
    )
    return db.execute(stmt).scalars().all()


@router.get("/documents/{document_id}/content", response_model=HostDocumentContentOut)
def get_document_content(
    document_id: uuid.UUID, host: Host = Depends(require_host), db: Session = Depends(get_db)
):
    document = db.get(Document, document_id)
    if document is None or document.structure_id != host.structure_id:
        raise HTTPException(status_code=404, detail="Document not found.")
    return document


@router.get("/faqs", response_model=list[FaqEntryOut])
def list_faqs(host: Host = Depends(require_host), db: Session = Depends(get_db)):
    return [
        FaqEntryOut(
            rank=e.rank,
            question=e.question,
            answer=e.answer,
            answer_language=e.answer_language,
        )
        for e in list_structure_faqs(db, host.structure_id)
    ]


@router.get("/analytics", response_model=AnalyticsOut)
def get_analytics(host: Host = Depends(require_host), db: Session = Depends(get_db)):
    """Question analytics aggregated across the whole structure ("General")."""
    return AnalyticsOut.from_unit_analytics(build_structure_analytics(db, host.structure_id))


@router.get("/units/{unit_id}/analytics", response_model=AnalyticsOut)
def get_unit_analytics(
    unit_id: uuid.UUID, host: Host = Depends(require_host), db: Session = Depends(get_db)
):
    """Question analytics for a single unit of the host's own structure."""
    unit = db.get(Unit, unit_id)
    if unit is None or unit.structure_id != host.structure_id:
        raise HTTPException(status_code=404, detail="Unit not found.")
    return AnalyticsOut.from_unit_analytics(build_unit_analytics(db, unit_id))


@router.get("/change-requests", response_model=list[ChangeRequestOut])
def list_change_requests(host: Host = Depends(require_host), db: Session = Depends(get_db)):
    stmt = (
        select(DocumentChangeRequest)
        .where(DocumentChangeRequest.host_id == host.id)
        .order_by(DocumentChangeRequest.created_at.desc())
    )
    requests = db.execute(stmt).scalars().all()
    admin_name = _admin_display_name(db)
    return [
        ChangeRequestOut.model_validate(r).model_copy(update={"admin_name": admin_name})
        for r in requests
    ]


@router.post("/change-requests", response_model=ChangeRequestOut, status_code=201)
def create_change_request(
    body: ChangeRequestCreate,
    host: Host = Depends(require_host),
    db: Session = Depends(get_db),
):
    if body.document_id is not None:
        document = db.get(Document, body.document_id)
        # The referenced document must belong to this host's structure.
        if document is None or document.structure_id != host.structure_id:
            raise HTTPException(status_code=404, detail="Document not found.")
    request = DocumentChangeRequest(
        structure_id=host.structure_id,
        host_id=host.id,
        document_id=body.document_id,
        title=body.title,
        body=body.body,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request
