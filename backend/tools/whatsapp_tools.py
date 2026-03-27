# tools/whatsapp_tools.py
# Twilio WhatsApp — user confirmation + team alert.
from __future__ import annotations

import asyncio
import structlog
from core.config import settings

logger = structlog.get_logger(__name__)

# Override in .env as TWILIO_WA_FROM for production numbers.
# Default is Twilio sandbox — must be approved for your account.
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

    @staticmethod
    def _normalize(phone: str) -> str:
        return phone if phone.startswith("+") else f"+{phone}"

    async def notify_user(self, state: dict) -> None:
        """Send confirmation WhatsApp to the lead after session completes."""
        if not self._ready():
            return
        phone = state.get("phone")
        if not phone:
            logger.warning("whatsapp_skip_no_user_phone")
            return

        name    = state.get("name") or "there"
        issue   = (state.get("issue") or state.get("pest_type") or "your request")
        address = state.get("address") or "your location"
        score   = (state.get("score") or "warm").upper()

        # Include appointment confirmation if booked
        appt_line = ""
        if state.get("appt_confirmed"):
            appt_line = f"\nAppointment: {state['appt_confirmed']}"
        elif state.get("appt_booked"):
            appt_line = "\nAppointment: confirmed — we'll call to confirm the time."

        msg = (
            f"Hi {name}! \u2705 Your request has been received.\n\n"
            f"Issue: {issue}\n"
            f"Location: {address}\n"
            f"Priority: {score}"
            f"{appt_line}\n\n"
            f"A technician will call you within 15 minutes. "
            f"Questions? Reply to this message."
        )

        try:
            client = self._client()
            await asyncio.to_thread(
                client.messages.create,
                from_=_TWILIO_WA_FROM,
                to=f"whatsapp:{self._normalize(phone)}",
                body=msg,
            )
            logger.info("whatsapp_user_sent", phone=phone)
        except Exception as exc:
            logger.error("whatsapp_user_failed", error=str(exc))

    async def notify_team(self, state: dict) -> None:
        """
        Send lead alert WhatsApp to the business owner.

        BUG FIX: was using TWILIO_FROM_NUMBER (the SMS sender) as the team
        receive number. These are different — TWILIO_FROM_NUMBER is the `from_`
        address for outbound SMS, not the number that receives the alert.
        Now uses TEAM_WHATSAPP_NUMBER with fallback to TEAM_PHONE.
        Add TEAM_WHATSAPP_NUMBER=+1... to your .env.
        """
        if not self._ready():
            return
        if state.get("score") not in ("hot", "warm"):
            return

        # TEAM_WHATSAPP_NUMBER = the number that RECEIVES team alerts
        team_phone = (
            getattr(settings, "TEAM_WHATSAPP_NUMBER", None)
            or getattr(settings, "TEAM_PHONE", None)
        )
        if not team_phone:
            logger.warning("whatsapp_team_skip_no_team_phone",
                           hint="Set TEAM_WHATSAPP_NUMBER in .env")
            return

        score   = (state.get("score") or "warm").upper()
        name    = state.get("name") or "Unknown"
        phone   = state.get("phone") or "—"
        issue   = state.get("issue") or state.get("pest_type") or "—"
        address = state.get("address") or "—"
        summary = state.get("ai_summary") or "—"
        appt    = state.get("appt_confirmed") or ("booked" if state.get("appt_booked") else "none")

        msg = (
            f"\U0001f525 *{score} LEAD*\n\n"
            f"*Name:* {name}\n"
            f"*Phone:* {phone}\n"
            f"*Issue:* {issue}\n"
            f"*Location:* {address}\n"
            f"*Appointment:* {appt}\n"
            f"*Summary:* {summary}"
        )

        try:
            client = self._client()
            await asyncio.to_thread(
                client.messages.create,
                from_=_TWILIO_WA_FROM,
                to=f"whatsapp:{self._normalize(team_phone)}",
                body=msg,
            )
            logger.info("whatsapp_team_sent", score=score)
        except Exception as exc:
            logger.error("whatsapp_team_failed", error=str(exc))

    async def send_lead_notification(self, state: dict) -> None:
        """Convenience: fire both user + team in parallel."""
        await asyncio.gather(
            self.notify_user(state),
            self.notify_team(state),
            return_exceptions=True,
        )


whatsapp_tools = WhatsAppTools()