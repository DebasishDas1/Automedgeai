# tools/whatsapp_tools.py
# Twilio WhatsApp notifications for chat leads.
# 
# Requires: uv add twilio
# Env vars: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, 
#           TWILIO_WA_FROM (e.g. whatsapp:+1...), 
#           TEAM_WHATSAPP_NUMBER
from __future__ import annotations

import asyncio
import structlog
from typing import Optional
from core.config import settings

logger = structlog.get_logger(__name__)


class WhatsAppTools:
    """Consolidated Twilio messaging logic for chat leads (SMS & WhatsApp)."""

    @staticmethod
    def _client(app_state=None):
        if app_state and hasattr(app_state, "twilio") and app_state.twilio:
            return app_state.twilio
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            from twilio.rest import Client
            return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        return None

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        if not phone: return ""
        clean = "".join(filter(str.isdigit, phone))
        return f"+{clean}" if not phone.startswith("+") else phone

    @classmethod
    async def _send_sms(cls, to: str, body: str, app_state=None) -> bool:
        """Generic SMS sender using the singleton client."""
        client = cls._client(app_state)
        if not client:
            logger.warning("sms_skip_no_client", to=to)
            return False
        try:
            await asyncio.to_thread(
                client.messages.create,
                from_=settings.TWILIO_FROM_NUMBER,
                to=cls._normalize_phone(to),
                body=body
            )
            return True
        except Exception as exc:
            logger.error(
                "sms_failed",
                error_type=type(exc).__name__,
                to=to[:10] if len(to) > 10 else to,
            )
            return False

    @classmethod
    async def notify_user(cls, state: dict, app_state=None) -> bool:
        """Send confirmation WhatsApp to the user."""
        phone = state.get("phone")
        if not phone: return False

        wa_from = getattr(settings, "TWILIO_WA_FROM", "whatsapp:+14155238886")
        to_num = cls._normalize_phone(phone)
        if not to_num.startswith("whatsapp:"): to_num = f"whatsapp:{to_num}"

        msg = (
            f"Hi {state.get('name', 'there')}, thank you for reaching out to {settings.CLINIC_NAME}! "
            f"We've received your request regarding {state.get('issue', 'service')}. "
            f"One of our specialists will call you shortly."
        )

        try:
            client = cls._client(app_state)
            if not client: return False
            await asyncio.to_thread(client.messages.create, from_=wa_from, to=to_num, body=msg)
            logger.info("wa_sent_to_user", to=to_num)
            return True
        except Exception as exc:
            logger.error(
                "wa_user_failed",
                error_type=type(exc).__name__,
            )
            return False

    @classmethod
    async def notify_team(cls, state: dict, app_state=None) -> bool:
        """Send lead alert WhatsApp to the business team."""
        team_phone = settings.TEAM_WHATSAPP_NUMBER
        if not team_phone: return False

        wa_from = getattr(settings, "TWILIO_WA_FROM", "whatsapp:+14155238886")
        to_num = cls._normalize_phone(team_phone)
        if not to_num.startswith("whatsapp:"): to_num = f"whatsapp:{to_num}"

        score = (state.get("score") or "warm").upper()
        msg = (
            f"\U0001f6a8 *New {score} Lead*\n\n"
            f"*Name:* {state.get('name') or '—'}\n"
            f"*Phone:* {state.get('phone') or '—'}\n"
            f"*Issue:* {state.get('issue') or '—'}\n"
            f"*Summary:* {state.get('ai_summary') or '—'}\n\n"
            f"View in CRM for full transcript."
        )
        try:
            client = cls._client(app_state)
            if not client: return False
            await asyncio.to_thread(client.messages.create, from_=wa_from, to=to_num, body=msg)
            logger.info("wa_sent_to_team", to=to_num)
            return True
        except Exception as exc:
            logger.error(
                "wa_team_failed",
                error_type=type(exc).__name__,
            )
            return False

    # ── Vertical Helpers ──────────────────────────────────────────────────────

    @classmethod
    async def send_insurance_reminder(cls, state: dict, app_state=None) -> bool:
        """Roofing: Send insurance claim process reminder."""
        phone = state.get("phone")
        if not phone: return False
        body = (
            f"Hi {state.get('name', 'there')}! Roof inspection coming up. "
            "Handy tip: have your homeowners insurance policy number ready—"
            "our inspector can help walk you through the claim process."
        )
        ok = await cls._send_sms(phone, body, app_state)
        if ok: logger.info("roofing_insurance_sms_sent", session_id=state.get("session_id"))
        return ok

    @classmethod
    async def send_emergency_alert(cls, state: dict, app_state=None) -> bool:
        """Plumbing/HVAC: Send rapid response confirmation."""
        phone = state.get("phone")
        if not phone: return False
        body = (
            f"Emergency dispatch confirmed to {state.get('address', 'your location')}. "
            "Please keep your main shutoff VALVE CLOSED if leaking. "
            "A technician will call you in 15 minutes."
        )
        ok = await cls._send_sms(phone, body, app_state)
        if ok: logger.info("emergency_sms_sent", session_id=state.get("session_id"))
        return ok

    @classmethod
    async def send_fallback_sms(cls, state: dict, app_state=None) -> bool:
        """Internal: Fallback when complex delivery pipelines fail."""
        phone = state.get("phone")
        if not phone: return False
        body = (
            "Apologies, we're having trouble processing your online request. "
            f"Please call our priority line directly: {settings.BUSINESS_PHONE}."
        )
        return await cls._send_sms(phone, body, app_state)


whatsapp_tools = WhatsAppTools()