# tools/booking_tools.py
from __future__ import annotations

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import Booking
from models.booking import BookingCreate, BookingResponse

logger = logging.getLogger(__name__)


async def create_booking(db: AsyncSession, data: BookingCreate) -> BookingResponse:
    """
    Persist a demo booking and fire team notification email.

    BUG FIX: _notify_team() is a synchronous Resend call. Calling it directly
    inside the async handler blocks the event loop for the full HTTP round-trip
    to Resend. Wrapped with asyncio.to_thread().

    BUG FIX: `import resend` at module top-level in the original raised
    ImportError on startup if the package was missing. Moved to lazy import
    inside send_email() so startup succeeds and the error surfaces at call time.
    """
    row = Booking(
        name=data.name,
        email=data.email,
        business=data.business,
        vertical=data.vertical,
        team_size=data.team_size,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)

    try:
        await asyncio.to_thread(_notify_team, data)
    except Exception as exc:
        logger.error("booking_notification_failed", error=str(exc))

    return BookingResponse.model_validate(row)


def send_email(to: str, subject: str, html: str, from_name: str = "automedge") -> dict:
    """
    BUG FIX: ENVIRONMENT check guards mock mode but RESEND_API_KEY check was
    INSIDE the else branch — unreachable when env != "prod". If RESEND_API_KEY
    is missing in prod, the call raises AttributeError on resend.api_key before
    the guard fires. Moved key check before the try block.
    """
    if settings.ENVIRONMENT != "prod":
        logger.info("[MOCK EMAIL] to=%s subject=%s", to, subject)
        return {"id": "mock_email", "status": "sent"}

    if not settings.RESEND_API_KEY:
        logger.warning("send_email_skip_no_api_key")
        return {"status": "error", "error": "missing api key"}

    try:
        import resend
        resend.api_key = settings.RESEND_API_KEY
        from_addr = getattr(settings, "EMAIL_FROM", "onboarding@resend.dev")
        response = resend.Emails.send({
            "from": f"{from_name} <{from_addr}>",
            "to": [to],
            "subject": subject,
            "html": html,
        })
        logger.info("email_sent", id=response["id"], to=to)
        return {"id": response["id"], "status": "sent"}
    except ImportError:
        raise RuntimeError("Run: uv add resend")
    except Exception as exc:
        logger.error("email_failed", to=to, error=str(exc))
        return {"id": None, "status": "error", "error": str(exc)}


def _notify_team(data: BookingCreate) -> None:
    """Synchronous team notification — always run via asyncio.to_thread."""
    html = f"""
<html><body style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px;">
  <h2 style="color:#0D1B2A;">New Demo Request</h2>
  <table>
    <tr><td style="color:#666;padding:4px 8px 4px 0;">Name</td>
        <td><strong>{data.name}</strong></td></tr>
    <tr><td style="color:#666;padding:4px 8px 4px 0;">Email</td>
        <td>{data.email}</td></tr>
    <tr><td style="color:#666;padding:4px 8px 4px 0;">Business</td>
        <td>{data.business}</td></tr>
    <tr><td style="color:#666;padding:4px 8px 4px 0;">Vertical</td>
        <td>{data.vertical}</td></tr>
    <tr><td style="color:#666;padding:4px 8px 4px 0;">Team Size</td>
        <td>{data.team_size or "—"}</td></tr>
  </table>
</body></html>"""
    send_email(
        to=settings.TEAM_EMAIL,
        subject=f"Demo request — {data.name} ({data.business})",
        html=html,
        from_name="automedge bookings",
    )