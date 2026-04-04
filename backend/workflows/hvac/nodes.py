# workflows/hvac/nodes.py
from __future__ import annotations

import time
import structlog

from tools.ai_tools import ai_tools
from workflows.shared import (
    build_validate_input_node,
    build_enrich_node,
    build_check_completion_node,
    build_chat_reply_node,
    build_delivery_node,
)
from workflows.base import field_missing
from workflows.hvac.prompts import HVAC_EXPERT_SYSTEM
from workflows.hvac.schema import LeadEnrichment, LeadScore
from workflows.hvac.state import HvacState

logger = structlog.get_logger(__name__)

_MAX_TURNS        = 10
_COLLECTED_FIELDS = ("issue", "description", "urgency", "address", "name", "phone", "email")
_REQUIRED_FIELDS  = ("issue", "urgency", "address")


def _migrate_legacy_fields(state: dict) -> None:
    """Fix old sessions that used 'location' instead of 'address'."""
    if field_missing(state, "address") and state.get("location"):
        state["address"] = state.pop("location")


# ── 1. Validate ───────────────────────────────────────────────────────────────
node_validate_input = build_validate_input_node(_MAX_TURNS, migrate_fn=_migrate_legacy_fields)

# ── 2. Enrich ─────────────────────────────────────────────────────────────────
node_enrich_lead = build_enrich_node(
    extract_fn=ai_tools.extract_fields,
    required_fields=_REQUIRED_FIELDS,
    collected_fields=_COLLECTED_FIELDS,
)

# ── 3. Check completion ───────────────────────────────────────────────────────
node_check_completion = build_check_completion_node(_REQUIRED_FIELDS)

# ── 4. Chat reply ─────────────────────────────────────────────────────────────
node_chat_reply = build_chat_reply_node(HVAC_EXPERT_SYSTEM, _COLLECTED_FIELDS)


# ── 5. Score ──────────────────────────────────────────────────────────────────
async def node_score_lead(state: HvacState) -> HvacState:
    start = time.perf_counter()
    state["last_node"] = "score_lead"

    urgency_for_score = state.get("urgency") or state.get("ai_urgency", "normal")

    snapshot = LeadEnrichment(
        name=state.get("name"),
        email=state.get("email"),
        phone=state.get("phone"),
        issue=state.get("issue"),
        urgency=urgency_for_score,
        intent=state.get("intent", "service_request"),
        is_spam=state.get("is_spam", False),
        summary=state.get("ai_summary") or "Lead captured",
    )

    try:
        score_data: LeadScore = await ai_tools.score_lead(snapshot)
        state["score"]        = score_data.score
        state["score_reason"] = score_data.score_reason
        state["next_step"]    = score_data.next_step
    except Exception as exc:
        logger.error("score_lead_failed", error=str(exc), sid=state.get("session_id"))
        state["score"]        = "warm"
        state["score_reason"] = "Scoring failed — defaulted to warm."
        state["next_step"]    = "schedule_callback"

    state["duration_ms"] = int((time.perf_counter() - start) * 1000)
    return state


# ── 6. Deliver ────────────────────────────────────────────────────────────────
node_finalize_and_deliver = build_delivery_node(vertical="hvac")