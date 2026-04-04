# workflows/plumbing/nodes.py
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
from workflows.plumbing.prompts import PLUMBING_EXPERT_SYSTEM
from workflows.plumbing.state import PlumbingState
from workflows.hvac.schema import LeadEnrichment, LeadScore

logger = structlog.get_logger(__name__)

_MAX_TURNS = 10

_COLLECTED_FIELDS = (
    "issue", "issue_type", "problem_area", "has_water_damage",
    "is_getting_worse", "main_shutoff_off", "is_homeowner",
    "property_type", "address", "urgency", "name", "phone", "email",
    "wants_appointment", "appt_confirmed", "description",
)

_REQUIRED_FIELDS = ("issue", "address")

_EMERGENCY_KEYWORDS = {
    "burst", "flooding", "flood", "sewage", "spraying",
    "overflow", "no water", "water everywhere", "water damage",
}


def _is_emergency(state: dict) -> bool:
    issue = (state.get("issue") or "").lower()
    issue_type = state.get("issue_type", "")
    urgency = state.get("urgency") or state.get("ai_urgency", "")
    return (
        issue_type == "emergency"
        or urgency == "emergency"
        or any(kw in issue for kw in _EMERGENCY_KEYWORDS)
        or bool(state.get("has_water_damage") and state.get("is_getting_worse"))
    )


# ── 1. Validate ───────────────────────────────────────────────────────────────
node_validate_input = build_validate_input_node(_MAX_TURNS)

# ── 2. Enrich ─────────────────────────────────────────────────────────────────
node_enrich_lead = build_enrich_node(
    extract_fn=ai_tools.extract_plumbing_fields,
    required_fields=_REQUIRED_FIELDS,
    collected_fields=_COLLECTED_FIELDS,
    is_emergency_fn=_is_emergency,
)

# ── 3. Check completion ───────────────────────────────────────────────────────
node_check_completion = build_check_completion_node(_REQUIRED_FIELDS)

# ── 4. Chat reply ─────────────────────────────────────────────────────────────
node_chat_reply = build_chat_reply_node(PLUMBING_EXPERT_SYSTEM, _COLLECTED_FIELDS)


# ── 5. Score ──────────────────────────────────────────────────────────────────
async def node_score_lead(state: PlumbingState) -> PlumbingState:
    start = time.perf_counter()
    state["last_node"] = "score_lead"

    if _is_emergency(state):
        state["score"]        = "hot"
        state["score_reason"] = "Emergency plumbing — immediate dispatch."
        state["next_step"]    = "immediate_dispatch"
        state["duration_ms"]  = int((time.perf_counter() - start) * 1000)
        return state

    urgency = state.get("urgency") or state.get("ai_urgency", "normal")
    urgency_map = {
        "emergency": "emergency", "urgent": "high",
        "routine": "normal", "normal": "normal",
    }

    snapshot = LeadEnrichment(
        name=state.get("name"),
        email=state.get("email"),
        phone=state.get("phone"),
        issue=state.get("issue"),
        urgency=urgency_map.get(urgency, "normal"),
        intent=state.get("intent", "service_request"),
        is_spam=state.get("is_spam", False),
        summary=state.get("ai_summary") or "Plumbing lead",
    )

    try:
        score_data: LeadScore = await ai_tools.score_lead(snapshot)
        state["score"]        = score_data.score
        state["score_reason"] = score_data.score_reason
        state["next_step"]    = score_data.next_step
    except Exception as exc:
        logger.error("plumbing_score_failed", error=str(exc), sid=state.get("session_id"))
        state["score"]        = "warm"
        state["score_reason"] = "Scoring failed — defaulted to warm."
        state["next_step"]    = "schedule_callback"

    state["duration_ms"] = int((time.perf_counter() - start) * 1000)
    return state


# ── 6. Deliver ────────────────────────────────────────────────────────────────

async def _send_emergency_sms(state: dict) -> None:
    if _is_emergency(state) and state.get("phone"):
        from tools.whatsapp_tools import whatsapp_tools
        await whatsapp_tools.send_emergency_alert(state, state.get("_app_state"))

node_finalize_and_deliver = build_delivery_node(
    vertical="plumbing",
    emergency_sms_fn=_send_emergency_sms,
)