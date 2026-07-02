"""Best-effort notifications for new visit-request leads.

Sending is entirely optional and never blocks (or fails) the request that
triggered it: if SMTP is not configured, or the send raises, we simply log and
move on. The lead is always persisted, so nothing is lost either way.
"""

import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.config import settings
from app.models.visit_request import VisitRequest

logger = logging.getLogger(__name__)


def _format_body(req: VisitRequest) -> str:
    lines = [
        "New visit request from the iGuest landing page:",
        "",
        f"Structure:     {req.structure_name}",
        f"City:          {req.city or '—'}",
        f"Business type: {req.business_type or '—'}",
        f"Contact:       {req.contact_name}",
        f"Email:         {req.contact_email}",
        f"Preferred date:{req.preferred_date or '—'}",
        "",
        "Review it in the admin panel → Requests → Visit requests.",
    ]
    return "\n".join(lines)


def notify_visit_request(req: VisitRequest) -> None:
    """Email the configured recipient about a new lead. Never raises."""
    recipient = settings.visit_request_notify_email.strip()
    if not recipient or not settings.smtp_host.strip():
        logger.info(
            "New visit request from %s (%s); email notifications not configured.",
            req.contact_name,
            req.contact_email,
        )
        return

    try:
        msg = EmailMessage()
        msg["Subject"] = f"New visit request — {req.structure_name}"
        msg["From"] = settings.smtp_from or settings.smtp_user or recipient
        msg["To"] = recipient
        msg["Reply-To"] = req.contact_email
        msg.set_content(_format_body(req))

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls(context=ssl.create_default_context())
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(msg)
        logger.info("Visit-request notification emailed to %s.", recipient)
    except Exception:  # pragma: no cover - best effort, must never break the request
        logger.exception("Failed to email visit-request notification (lead is still stored).")
