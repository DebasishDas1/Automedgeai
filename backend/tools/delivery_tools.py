# services/delivery_tools.py
# Orchestrates the full post-chat delivery pipeline:
#   classify → store (sheets) → notify (email + WhatsApp) → HubSpot CRM sync
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import structlog

from core.config import settings
from tools.sheets_tools import sheets_tools
from tools.email_tools import email_tools
from tools.whatsapp_tools import whatsapp_tools

logger = structlog.get_logger(__name__)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _full_conversation(state: dict) -> str:
    lines = []
    for m in state.get("messages", []):
        role = m.get("role", "").upper()
        lines.append(f"{role}: {m.get('content', '')}")
    return "\n".join(lines)


def _sheet_id_for_vertical(vertical: str) -> str | None:
    return {
        "hvac":         settings.HVAC_SHEET_ID,
        "plumbing":     settings.PLUMBING_SHEET_ID,
        "roofing":      settings.ROOFING_SHEET_ID,
        "pest_control": settings.PEST_SHEET_ID,
    }.get(vertical)


# ── Tool 1: classify ──────────────────────────────────────────────────────────

def classify_lead(state: dict) -> str:
    return state.get("score") or "warm"


# ── Tool 2: store in Sheets ───────────────────────────────────────────────────

async def store_lead(state: dict, score: str) -> bool:
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
        state.get("issue") or state.get("pest_type") or
            state.get("damage_type") or "—",
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
        )
        return True
    except Exception as exc:
        logger.error("store_lead_failed", error=str(exc))
        return False


# ── Tool 3: email notification ────────────────────────────────────────────────

async def send_email_notification(state: dict, score: str) -> bool:
    try:
        await email_tools.send_lead_notification(state, score)
        return True
    except Exception as exc:
        logger.error("email_notification_failed", error=str(exc))
        return False


# ── Tool 4: WhatsApp notification ─────────────────────────────────────────────

async def send_whatsapp_notification(state: dict, score: str) -> bool:
    try:
        await asyncio.gather(
            whatsapp_tools.notify_user(state),
            whatsapp_tools.notify_team(state),
            return_exceptions=True,
        )
        return True
    except Exception as exc:
        logger.error("whatsapp_notification_failed", error=str(exc))
        return False


# ── Tool 5: HubSpot CRM sync ──────────────────────────────────────────────────

async def sync_to_hubspot(state: dict) -> dict:
    """
    Sync completed lead to HubSpot:
      - Upsert contact (create or update by email)
      - Create deal linked to contact
      - Book meeting if appointment was confirmed
    Returns results dict. Never raises — failure is logged and ignored.
    """
    try:
        from tools.hubspot_tools import sync_lead_to_hubspot
        results = await sync_lead_to_hubspot(state)
        logger.info("hubspot_sync_ok",
            contact_id=results.get("contact_id"),
            deal_id=results.get("deal_id"),
            meeting_id=results.get("meeting_id"),
            session_id=state.get("session_id"),
        )
        return results
    except Exception as exc:
        logger.error("hubspot_sync_failed", error=str(exc),
                     session_id=state.get("session_id"))
        return {"contact_id": None, "deal_id": None, "meeting_id": None}


# ── Orchestrator ──────────────────────────────────────────────────────────────

async def run_delivery_pipeline(state: dict) -> dict:
    """
    Full post-chat delivery pipeline:
      classify → store (Sheets) → notify (Email + WhatsApp) → HubSpot CRM

    Each step is isolated — failure in one never blocks the rest.
    HubSpot runs last so CRM always gets the final enriched state.
    """
    session_id = state.get("session_id")
    log = logger.bind(session_id=session_id)

    results = {
        "score":      None,
        "stored":     False,
        "email_sent": False,
        "wa_sent":    False,
        "hubspot":    {},
    }

    # Step 1: Classify
    score = classify_lead(state)
    results["score"] = score
    log.info("delivery_pipeline_start", score=score)

    # Step 2: Sheets (must finish before notifications — provides audit trail)
    results["stored"] = await store_lead(state, score)

    # Step 3: Email + WhatsApp in parallel
    email_task = asyncio.create_task(send_email_notification(state, score))
    wa_task    = asyncio.create_task(send_whatsapp_notification(state, score))
    email_ok, wa_ok = await asyncio.gather(email_task, wa_task,
                                           return_exceptions=True)
    results["email_sent"] = email_ok is True
    results["wa_sent"]    = wa_ok is True

    # Step 4: HubSpot CRM sync (runs after notifications — non-blocking)
    results["hubspot"] = await sync_to_hubspot(state)

    log.info("delivery_pipeline_complete",
        score=score,
        stored=results["stored"],
        email_sent=results["email_sent"],
        wa_sent=results["wa_sent"],
        hs_contact=results["hubspot"].get("contact_id"),
        hs_deal=results["hubspot"].get("deal_id"),
        hs_meeting=results["hubspot"].get("meeting_id"),
    )
    return results