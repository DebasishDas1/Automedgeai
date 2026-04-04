# workflows/roofing/nodes.py
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
from workflows.roofing.prompts import ROOFING_EXPERT_SYSTEM
from workflows.roofing.state import RoofingState
from workflows.hvac.schema import LeadEnrichment, LeadScore

logger = structlog.get_logger(__name__)

_MAX_TURNS = 10

_COLLECTED_FIELDS = (
    "damage_type", "damage_detail", "storm_date", "roof_age",
    "has_interior_leak", "has_insurance", "insurance_contacted",
    "adjuster_involved", "is_homeowner", "property_type",
    "address", "urgency", "name", "phone", "email",
    "description",
)

_REQUIRED_FIELDS = ("damage_type", "address")

_STORM_KEYWORDS = {
    "hail", "hailstorm", " storm", "wind damage", "tree fell",
    "missing shingles", "granules", "adjuster", "insurance claim",
    "neighbor filed",
}


def _is_storm_lead(state: dict) -> bool:
    damage  = (state.get("damage_type") or "").lower()
    detail  = (state.get("damage_detail") or "").lower()
    urgency = (state.get("urgency") or state.get("ai_urgency") or "").lower()
    return (
        damage == "storm"
        or urgency == "storm_damage"
        or state.get("adjuster_involved")
        or state.get("insurance_contacted")
        or any(kw in detail for kw in _STORM_KEYWORDS)
    )


def _is_high_value(state: dict) -> bool:
    return (
        _is_storm_lead(state)
        and state.get("has_insurance")
        and state.get("is_homeowner") is not False
    )


# ── 1. Validate ───────────────────────────────────────────────────────────────
node_validate_input = build_validate_input_node(_MAX_TURNS)

# ── 2. Enrich ─────────────────────────────────────────────────────────────────
node_enrich_lead = build_enrich_node(
    extract_fn=ai_tools.extract_roofing_fields,
    required_fields=_REQUIRED_FIELDS,
    collected_fields=_COLLECTED_FIELDS,
    is_emergency_fn=_is_storm_lead,
)

# ── 3. Check completion ───────────────────────────────────────────────────────
node_check_completion = build_check_completion_node(_REQUIRED_FIELDS)

# ── 4. Chat reply ─────────────────────────────────────────────────────────────
node_chat_reply = build_chat_reply_node(ROOFING_EXPERT_SYSTEM, _COLLECTED_FIELDS)


# ── 5. Score ──────────────────────────────────────────────────────────────────
async def node_score_lead(state: RoofingState) -> RoofingState:
    start = time.perf_counter()
    state["last_node"] = "score_lead"

    if _is_high_value(state):
        bonus = " Adjuster involved." if state.get("adjuster_involved") else ""
        state["score"]        = "hot"
        state["score_reason"] = f"Storm damage + insurance + homeowner.{bonus}"
        state["next_step"]    = "immediate_dispatch"
        state["duration_ms"]  = int((time.perf_counter() - start) * 1000)
        return state

    if _is_storm_lead(state) and not state.get("has_insurance"):
        state["score"]        = "warm"
        state["score_reason"] = "Storm damage, insurance status unknown."
        state["next_step"]    = "schedule_callback"
        state["duration_ms"]  = int((time.perf_counter() - start) * 1000)
        return state

    urgency_map = {
        "storm_damage": "emergency", "leak_active": "high",
        "inspection_needed": "normal", "planning": "low",
    }
    urgency = state.get("urgency") or state.get("ai_urgency", "planning")
    mapped  = urgency_map.get(urgency, "normal")

    snapshot = LeadEnrichment(
        name=state.get("name"), email=state.get("email"),
        phone=state.get("phone"), issue=state.get("damage_type") or "roofing inquiry",
        urgency=mapped, intent=state.get("intent", "service_request"),
        is_spam=state.get("is_spam", False),
        summary=state.get("ai_summary") or "Roofing lead",
    )

    try:
        score_data: LeadScore = await ai_tools.score_lead(snapshot)
        state["score"]        = score_data.score
        state["score_reason"] = score_data.score_reason
        state["next_step"]    = score_data.next_step
    except Exception as exc:
        logger.error("roofing_score_failed", error=str(exc), sid=state.get("session_id"))
        state["score"]        = "warm"
        state["score_reason"] = "Scoring failed — defaulted to warm."
        state["next_step"]    = "schedule_callback"

    state["duration_ms"] = int((time.perf_counter() - start) * 1000)
    return state


# ── 6. Deliver ────────────────────────────────────────────────────────────────

async def _send_storm_sms(state: dict) -> None:
    if _is_storm_lead(state) and state.get("has_insurance") and state.get("phone"):
        from tools.whatsapp_tools import whatsapp_tools
        await whatsapp_tools.send_insurance_reminder(state, state.get("_app_state"))

node_finalize_and_deliver = build_delivery_node(
    vertical="roofing",
    emergency_sms_fn=_send_storm_sms,
)