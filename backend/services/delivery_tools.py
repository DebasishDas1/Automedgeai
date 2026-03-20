# services/delivery_tools.py
# Orchestrates the full post-chat delivery pipeline:
#   classify → store (sheets) → notify (email + WhatsApp)
#
# All tools are independent — failure of one never blocks the others.
# Called by node_finalize_and_deliver in nodes.py.
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import structlog

from core.config import settings
from services.sheets_service import sheets_service
from services.email_service import email_service
from services.whatsapp_service import whatsapp_service

logger = structlog.get_logger(__name__)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _full_conversation(state: dict) -> str:
    """Format messages as readable transcript."""
    lines = []
    for m in state.get("messages", []):
        role = m.get("role", "").upper()
        content = m.get("content", "")
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def _sheet_id_for_vertical(vertical: str) -> str | None:
    """Map vertical to its configured sheet ID."""
    return {
        "hvac":         settings.HVAC_SHEET_ID,
        "plumbing":     settings.PLUMBING_SHEET_ID,
        "roofing":      settings.ROOFING_SHEET_ID,
        "pest_control": settings.PEST_SHEET_ID,
    }.get(vertical)


# ── Tool 1: classify_lead ─────────────────────────────────────────────────────
# Classification already done by ai_service during the conversation.
# This tool just reads the score from state — no extra LLM call needed.

def classify_lead(state: dict) -> str:
    """Returns 'hot' | 'warm' | 'cold' from existing state score."""
    return state.get("score") or "warm"


# ── Tool 2: store_lead ────────────────────────────────────────────────────────

async def store_lead(state: dict, score: str) -> bool:
    """Store lead in the correct Google Sheet tab."""
    vertical = state.get("vertical", "hvac")
    sheet_id = _sheet_id_for_vertical(vertical)

    if not sheet_id:
        logger.warning("store_lead_skip_no_sheet_id", vertical=vertical)
        return False

    tab_name = f"{score.capitalize()} Leads"  # "Hot Leads" / "Warm Leads" / "Cold Leads"

    row = [
        _utcnow(),
        state.get("name") or "Anonymous",
        state.get("email") or "—",
        state.get("phone") or "—",
        state.get("issue") or "—",
        state.get("description") or "—",
        state.get("urgency") or state.get("ai_urgency") or "—",
        state.get("address") or "—",
        score.upper(),
        state.get("ai_summary") or "—",
        _full_conversation(state),
        state.get("session_id") or "—",
    ]

    try:
        await sheets_service.append_lead(
            sheet_id=sheet_id,
            tab_name=tab_name,
            row_data=row,
        )
        logger.info("store_lead_ok", score=score, tab=tab_name)
        return True
    except Exception as exc:
        logger.error("store_lead_failed", error=str(exc))
        return False


# ── Tool 3: send_email_notification ──────────────────────────────────────────

async def send_email_notification(state: dict, score: str) -> bool:
    try:
        await email_service.send_lead_notification(state, score)
        return True
    except Exception as exc:
        logger.error("email_notification_failed", error=str(exc))
        return False


# ── Tool 4: send_whatsapp_notification ────────────────────────────────────────

async def send_whatsapp_notification(state: dict, score: str) -> bool:
    try:
        # Run user confirmation + team alert in parallel
        await asyncio.gather(
            whatsapp_service.notify_user(state),
            whatsapp_service.notify_team(state),
            return_exceptions=True,
        )
        return True
    except Exception as exc:
        logger.error("whatsapp_notification_failed", error=str(exc))
        return False


# ── Orchestrator ──────────────────────────────────────────────────────────────

async def run_delivery_pipeline(state: dict) -> dict:
    """
    Main entry point called by node_finalize_and_deliver.
    Runs: classify → store → notify (email + WhatsApp in parallel).
    Each step is isolated — failure never blocks the next.

    Returns a results dict for logging/debugging.
    """
    session_id = state.get("session_id")
    log = logger.bind(session_id=session_id)

    results = {
        "score":      None,
        "stored":     False,
        "email_sent": False,
        "wa_sent":    False,
    }

    # Step 1: Classify
    score = classify_lead(state)
    results["score"] = score
    log.info("delivery_pipeline_start", score=score)

    # Step 2: Store in Sheets (must complete before notifications)
    results["stored"] = await store_lead(state, score)

    # Step 3: Email + WhatsApp in parallel (non-blocking)
    email_task = asyncio.create_task(send_email_notification(state, score))
    wa_task    = asyncio.create_task(send_whatsapp_notification(state, score))

    email_ok, wa_ok = await asyncio.gather(email_task, wa_task, return_exceptions=True)
    results["email_sent"] = email_ok is True
    results["wa_sent"]    = wa_ok is True

    log.info("delivery_pipeline_complete", **results)
    return results