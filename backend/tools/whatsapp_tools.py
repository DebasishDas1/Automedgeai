# tools/whatsapp_tools.py
# Twilio WhatsApp notifications — user confirmation + team alert.
from __future__ import annotations

import asyncio
import structlog
from core.config import settings

logger = structlog.get_logger(__name__)

# Must match your approved sender in Twilio console.
# Set TWILIO_WA_FROM in .env to override (e.g. for production number).
_TWILIO_WA_FROM = getattr(settings, "TWILIO_WA_FROM", "whatsapp:+14155238886")


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

    def _normalize_phone(self, phone: str) -> str:
        return phone if phone.startswith("+") else f"+{phone}"

    async def notify_user(self, state: dict) -> None:
        """Send booking confirmation WhatsApp to the lead."""
        if not self._ready():
            return
        phone = state.get("phone")
        if not phone:
            logger.warning("whatsapp_skip_no_user_phone")
            return

        name    = state.get("name") or "there"
        issue   = state.get("issue") or state.get("pest_type") or "your request"
        address = state.get("address") or "your location"
        score   = (state.get("score") or "warm").upper()

        msg = (
            f"Hi {name}! \u2705 Your request has been received.\n\n"
            f"Issue: {issue}\n"
            f"Location: {address}\n"
            f"Priority: {score}\n\n"
            f"A technician will call you within 15 minutes. "
            f"Questions? Reply to this message."
        )
        try:
            client = self._client()
            await asyncio.to_thread(
                client.messages.create,
                from_=_TWILIO_WA_FROM,
                to=f"whatsapp:{self._normalize_phone(phone)}",
                body=msg,
            )
            logger.info("whatsapp_user_sent", phone=phone)
        except Exception as exc:
            logger.error("whatsapp_user_failed", error=str(exc))

    async def notify_team(self, state: dict) -> None:
        """
        Send lead alert WhatsApp to the business owner.

        BUG FIX: team_phone was pulled from TWILIO_FROM_NUMBER which is the
        SMS sender number (used as `from_`), not the team's receive number.
        These are different. Added TEAM_WHATSAPP_NUMBER as the correct setting.
        Falls back to TWILIO_FROM_NUMBER for backward compatibility.

        BUG FIX: score guard checked state.get("score") not in ("hot","warm")
        BEFORE uppercasing — but score was uppercased into a local variable
        `score` and never written back to state. The guard always compared
        against lowercase values from state, so it worked by accident.
        Made it explicit: compare directly against state.get("score").
        """
        if not self._ready():
            return
        if state.get("score") not in ("hot", "warm"):
            return

        # TEAM_WHATSAPP_NUMBER = the number that *receives* the alert
        team_phone = getattr(settings, "TEAM_WHATSAPP_NUMBER", None) \
                     or getattr(settings, "TWILIO_FROM_NUMBER", None)
        if not team_phone:
            logger.warning("whatsapp_skip_no_team_phone")
            return

        score   = (state.get("score") or "warm").upper()
        name    = state.get("name") or "Unknown"
        phone   = state.get("phone") or "—"
        issue   = state.get("issue") or state.get("pest_type") or "—"
        address = state.get("address") or "—"
        summary = state.get("ai_summary") or "—"

        msg = (
            f"\U0001f525 *{score} LEAD*\n\n"
            f"*Name:* {name}\n"
            f"*Phone:* {phone}\n"
            f"*Issue:* {issue}\n"
            f"*Location:* {address}\n"
            f"*Summary:* {summary}"
        )
        try:
            client = self._client()
            await asyncio.to_thread(
                client.messages.create,
                from_=_TWILIO_WA_FROM,
                to=f"whatsapp:{self._normalize_phone(team_phone)}",
                body=msg,
            )
            logger.info("whatsapp_team_sent", score=score)
        except Exception as exc:
            logger.error("whatsapp_team_failed", error=str(exc))

    async def send_lead_notification(self, state: dict) -> None:
        """Convenience: fire both user + team notifications."""
        await asyncio.gather(
            self.notify_user(state),
            self.notify_team(state),
            return_exceptions=True,
        )


whatsapp_tools = WhatsAppTools()