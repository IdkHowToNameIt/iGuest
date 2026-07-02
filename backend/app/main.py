import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import admin, geo, guest, host
from app.services.scheduler import faq_recompute_loop, retention_loop

UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the GDPR retention purge + FAQ/analytics recompute loops in the background
    stop_event = asyncio.Event()
    tasks = []
    if settings.retention_purge_enabled:
        tasks.append(asyncio.create_task(retention_loop(stop_event)))
        logger.info(
            "Retention purge scheduler started (interval=%ss).",
            settings.retention_purge_interval_seconds,
        )
    if settings.faq_recompute_enabled:
        tasks.append(asyncio.create_task(faq_recompute_loop(stop_event)))
        logger.info(
            "FAQ recompute scheduler started (interval=%ss).",
            settings.faq_recompute_interval_seconds,
        )
    try:
        yield
    finally:
        if tasks:
            stop_event.set()
            for task in tasks:
                task.cancel()
            for task in tasks:
                try:
                    await task
                except asyncio.CancelledError:
                    pass


app = FastAPI(title="iGuest API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(guest.router)
app.include_router(admin.login_router)
app.include_router(admin.router)
app.include_router(host.login_router)
app.include_router(host.router)
app.include_router(geo.router)

# Serves profile-picture uploads (see app/services/avatars.py); paths returned
# by the API (e.g. "/uploads/avatars/<file>") resolve directly against this.
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")


@app.get("/health")
def health():
    return {"status": "ok"}
