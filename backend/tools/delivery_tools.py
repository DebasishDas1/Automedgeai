# tools/delivery_tools.py
# Post-chat delivery pipeline: classify → Sheets → Email+WA (parallel) → HubSpot
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import structlog
from core.config import settings

logger = structlog.get_logger(__name__)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _full_conversation(state: dict) -> str:
    return "\n".join(
        f"{m.get('role', '').upper()}: {m.get('content', '')}"
        for m in state.get("messages", [])
    )


def _sheet_id_for_vertical(vertical: str) -> str | None:
    return {
        "hvac":         getattr(settings, "HVAC_SHEET_ID", None),
        "plumbing":     getattr(settings, "PLUMBING_SHEET_ID", None),
        "roofing":      getattr(settings, "ROOFING_SHEET_ID", None),
        "pest_control": getattr(settings, "PEST_SHEET_ID", None),
    }.get(vertical)


def _issue_field(state: dict) -> str:
    return state.get("issue") or state.get("pest_type") or state.get("damage_type") or "—"


def classify_lead(state: dict) -> str:
    return state.get("score") or "warm"


async def store_lead(state: dict, score: str, app_state=None) -> bool:
    from tools.sheets_tools import sheets_tools
    vertical = state.get("vertical", "hvac")
    sheet_id = _sheet_id_for_vertical(vertical)
    if not sheet_id:
        logger.warning("store_lead_skip_no_sheet_id", vertical=vertical)
        return False
    row = [
        _utcnow(),
        state.get("name") or "Anonymous",
        state.get("email") or "—",
        state.get("phone") or "—",
        _issue_field(state),
        state.get("description") or "—",
        state.get("urgency") or state.get("ai_urgency") or "—",
        state.get("address") or "—",
        score.upper(),
        state.get("ai_summary") or "—",
        _full_conversation(state),
        state.get("session_id") or "—",
    ]
    try:
        await sheets_tools.append_lead(
            sheet_id=sheet_id,
            tab_name=f"{score.capitalize()} Leads",
            row_data=row,
            app_state=app_state,
        )
        return True
    except Exception as exc:
        logger.error("store_lead_failed",
                     error_type=type(exc).__name__,
                     vertical=vertical, session_id=state.get("session_id")[:20] if state.get("session_id") else "unknown")
        return False


async def send_email_notification(state: dict, score: str, app_state=None) -> bool:
    try:
        from tools.email_tools import email_tools
        await email_tools.send_lead_notification(state, score, app_state=app_state)
        return True
    except Exception as exc:
        logger.error("email_notification_failed",
                     error_type=type(exc).__name__,
                     session_id=state.get("session_id")[:20] if state.get("session_id") else "unknown")
        return False


async def send_whatsapp_notification(state: dict, app_state=None) -> bool:
    """
    BUG FIX: original passed `score` param which notify_user/notify_team
    don't accept (they read score from state). Also had nested gather()
    inside a gather(), causing inner exceptions to be swallowed as results.
    """
    try:
        from tools.whatsapp_tools import whatsapp_tools
        await asyncio.gather(
            whatsapp_tools.notify_user(state, app_state=app_state),
            whatsapp_tools.notify_team(state, app_state=app_state),
            return_exceptions=True,
        )
        return True
    except Exception as exc:
        logger.error("whatsapp_notification_failed",
                     error_type=type(exc).__name__,
                     session_id=state.get("session_id")[:20] if state.get("session_id") else "unknown")
        return False


async def sync_to_hubspot(state: dict, app_state=None) -> dict:
    """
    BUG FIX: was importing sync_lead_to_hubspot as a bare function.
    hubspot_tools.py now exposes it via the HubSpotTools singleton.
    """
    try:
        from tools.hubspot_tools import hubspot_tools
        results = await hubspot_tools.sync_lead(state, app_state=app_state)
        logger.info("hubspot_sync_ok",
                    contact_id=results.get("contact_id"),
                    deal_id=results.get("deal_id"),
                    meeting_id=results.get("meeting_id"),
                    session_id=state.get("session_id"))
        return results
    except Exception as exc:
        logger.error("hubspot_sync_failed",
                     error_type=type(exc).__name__,
                     session_id=state.get("session_id")[:20] if state.get("session_id") else "unknown")
        return {"contact_id": None, "deal_id": None, "meeting_id": None}


async def run_delivery_pipeline(state: dict) -> dict:
    """Full post-chat delivery pipeline. Each step is isolated."""
    session_id = state.get("session_id")
    app_state  = state.get("_app_state")
    log = logger.bind(session_id=session_id, vertical=state.get("vertical"))

    results: dict = {
        "score":      None,
        "stored":     False,
        "email_sent": False,
        "wa_sent":    False,
        "hubspot":    {"contact_id": None, "deal_id": None, "meeting_id": None},
    }

    score = classify_lead(state)
    results["score"] = score
    log.info("delivery_pipeline_start", score=score)

    results["stored"] = await store_lead(state, score, app_state=app_state)

    email_ok, wa_ok = await asyncio.gather(
        send_email_notification(state, score, app_state=app_state),
        send_whatsapp_notification(state, app_state=app_state),
        return_exceptions=True,
    )
    results["email_sent"] = email_ok is True
    results["wa_sent"]    = wa_ok is True
    if isinstance(email_ok, Exception):
        log.error("email_gather_exc", error=str(email_ok))
    if isinstance(wa_ok, Exception):
        log.error("wa_gather_exc", error=str(wa_ok))

    results["hubspot"] = await sync_to_hubspot(state)

    log.info("delivery_pipeline_complete",
             score=score, stored=results["stored"],
             email_sent=results["email_sent"], wa_sent=results["wa_sent"],
             hs_contact=results["hubspot"].get("contact_id"),
             hs_deal=results["hubspot"].get("deal_id"),
             hs_meeting=results["hubspot"].get("meeting_id"))
    return results