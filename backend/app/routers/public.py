"""
Public API (no authentication — reachable by anyone on the landing page).

  POST /api/public/visit-requests  → submit a "book a visit" lead

Kept separate from the guest API (token-scoped) and the admin API (auth-gated)
because these endpoints are open to anyone: the landing page posts here without
any credentials.
"""

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import VisitRequest
from app.schemas.public import VisitRequestCreate, VisitRequestCreatedOut
from app.services.notifications import notify_visit_request

router = APIRouter(prefix="/api/public", tags=["public"])


@router.post("/visit-requests", response_model=VisitRequestCreatedOut, status_code=201)
def create_visit_request(
    body: VisitRequestCreate,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Store a landing-page lead and (best-effort, in the background) email it."""
    req = VisitRequest(**body.model_dump())
    db.add(req)
    db.commit()
    db.refresh(req)
    background.add_task(notify_visit_request, req)
    return VisitRequestCreatedOut(ok=True)
