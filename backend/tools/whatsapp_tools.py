# services/whatsapp_tools.py
# Twilio WhatsApp notifications — confirmation to user + alert to team.
from __future__ import annotations

import structlog
from core.config import settings

logger = structlog.get_logger(__name__)

# Twilio WhatsApp sender — must be approved in your Twilio console
_TWILIO_WA_FROM = "whatsapp:+14155238886"  # Twilio sandbox default


class WhatsAppTools:

    def _client(self):
        try:
            from twilio.rest import Client
        except ImportError:
            raise RuntimeError("Run: uv add twilio")
        return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    def _ready(self) -> bool:
        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
            logger.warning("whatsapp_skip_no_credentials")
            return False
        return True

    async def notify_user(self, state: dict) -> None:
        """Send booking confirmation WhatsApp to the user."""
        if not self._ready():
            return

        phone = state.get("phone")
        if not phone:
            logger.warning("whatsapp_skip_no_user_phone")
            return

        # Normalize phone — add + if missing
        if not phone.startswith("+"):
            phone = f"+{phone}"

        name    = state.get("name") or "there"
        issue   = state.get("issue") or "your HVAC issue"
        address = state.get("address") or "your location"
        score   = (state.get("score") or "warm").upper()

        msg = (
            f"Hi {name}! ✅ Your request has been received.\n\n"
            f"Issue: {issue}\n"
            f"Location: {address}\n"
            f"Priority: {score}\n\n"
            f"A technician will call you within 15 minutes. "
            f"Questions? Reply to this message."
        )

        try:
            import asyncio
            client = self._client()
            await asyncio.to_thread(
                client.messages.create,
                from_=_TWILIO_WA_FROM,
                to=f"whatsapp:{phone}",
                body=msg,
            )
            logger.info("whatsapp_user_sent", phone=phone)
        except Exception as exc:
            logger.error("whatsapp_user_failed", error=str(exc))

    async def notify_team(self, state: dict) -> None:
        """Send hot lead alert WhatsApp to the business owner."""
        if not self._ready():
            return

        team_phone = settings.TWILIO_FROM_NUMBER
        if not team_phone:
            logger.warning("whatsapp_skip_no_team_phone")
            return

        score   = (state.get("score") or "warm").upper()
        name    = state.get("name") or "Unknown"
        phone   = state.get("phone") or "—"
        issue   = state.get("issue") or "—"
        address = state.get("address") or "—"
        summary = state.get("ai_summary") or "—"

        # Only send team alert for hot leads
        if state.get("score") not in ("hot", "warm"):
            return

        msg = (
            f"🔥 *{score} LEAD*\n\n"
            f"*Name:* {name}\n"
            f"*Phone:* {phone}\n"
            f"*Issue:* {issue}\n"
            f"*Location:* {address}\n"
            f"*Summary:* {summary}"
        )

        try:
            import asyncio
            client = self._client()
            await asyncio.to_thread(
                client.messages.create,
                from_=_TWILIO_WA_FROM,
                to=f"whatsapp:{team_phone}",
                body=msg,
            )
            logger.info("whatsapp_team_sent", score=score)
        except Exception as exc:
            logger.error("whatsapp_team_failed", error=str(exc))


whatsapp_tools = WhatsAppTools()