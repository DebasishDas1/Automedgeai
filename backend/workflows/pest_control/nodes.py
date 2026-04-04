# workflows/pest_control/nodes.py
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
from workflows.pest_control.prompts import PEST_EXPERT_SYSTEM
from workflows.pest_control.state import PestState
from workflows.hvac.schema import LeadEnrichment, LeadScore

logger = structlog.get_logger(__name__)

_MAX_TURNS = 10

_COLLECTED_FIELDS = (
    "pest_type", "infestation_area", "duration", "has_damage",
    "tried_treatment", "is_homeowner", "property_type", "address",
    "urgency", "wants_annual", "name", "phone", "email",
    "description",
)

_REQUIRED_FIELDS = ("pest_type", "address")


# ── 1. Validate ───────────────────────────────────────────────────────────────
node_validate_input = build_validate_input_node(_MAX_TURNS)

# ── 2. Enrich ─────────────────────────────────────────────────────────────────
node_enrich_lead = build_enrich_node(
    extract_fn=ai_tools.extract_pest_fields,
    required_fields=_REQUIRED_FIELDS,
    collected_fields=_COLLECTED_FIELDS,
)

# ── 3. Check completion ───────────────────────────────────────────────────────
node_check_completion = build_check_completion_node(_REQUIRED_FIELDS)

# ── 4. Chat reply ─────────────────────────────────────────────────────────────
node_chat_reply = build_chat_reply_node(PEST_EXPERT_SYSTEM, _COLLECTED_FIELDS)


# ── 5. Score ──────────────────────────────────────────────────────────────────
async def node_score_lead(state: PestState) -> PestState:
    start = time.perf_counter()
    state["last_node"] = "score_lead"

    urgency = state.get("urgency") or state.get("ai_urgency", "normal")
    urgency_map = {"high": "high", "medium": "normal", "low": "low"}
    mapped_urgency = urgency_map.get(urgency, "normal")

    snapshot = LeadEnrichment(
        name=state.get("name"),
        email=state.get("email"),
        phone=state.get("phone"),
        issue=state.get("pest_type"),
        urgency=mapped_urgency,
        intent=state.get("intent", "service_request"),
        is_spam=state.get("is_spam", False),
        summary=state.get("ai_summary") or "Pest control lead",
    )

    try:
        score_data: LeadScore = await ai_tools.score_lead(snapshot)
        state["score"]        = score_data.score
        state["score_reason"] = score_data.score_reason
        state["next_step"]    = score_data.next_step
    except Exception as exc:
        logger.error("pest_score_failed", error=str(exc), sid=state.get("session_id"))
        state["score"]        = "warm"
        state["score_reason"] = "Scoring failed — defaulted to warm."
        state["next_step"]    = "schedule_callback"

    state["duration_ms"] = int((time.perf_counter() - start) * 1000)
    return state


# ── 6. Deliver ────────────────────────────────────────────────────────────────
node_finalize_and_deliver = build_delivery_node(vertical="pest_control")