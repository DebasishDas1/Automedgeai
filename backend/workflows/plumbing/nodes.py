# workflows/plumbing/nodes.py
from __future__ import annotations

import time
from datetime import datetime, timezone

import structlog
from langchain_core.messages import SystemMessage

from core.database import Lead, get_db_context
from llm import llm
from tools.ai_tools import ai_tools
from workflows.shared import build_validate_input_node, build_check_completion_node, build_chat_reply_node
from workflows.base import build_lc_messages, field_missing, get_appt_slots
from workflows.hvac.schema import LeadEnrichment, LeadScore
from workflows.plumbing.prompts import PLUMBING_EXPERT_SYSTEM
from workflows.plumbing.state import PlumbingState
from langchain_core.messages import HumanMessage, SystemMessage

logger = structlog.get_logger(__name__)

_MAX_TURNS = 10

_COLLECTED_FIELDS = (
    "issue", "issue_type", "problem_area", "has_water_damage",
    "is_getting_worse", "main_shutoff_off", "is_homeowner",
    "property_type", "address", "urgency", "name", "phone", "email",
)

# Minimum fields to complete session.
# issue + address covers both emergency (dispatch) and routine (schedule).
# name/phone/email come from the form.
_REQUIRED_FIELDS = ("issue", "address")

# Emergency keywords for fast-path detection (zero LLM call)
_EMERGENCY_KEYWORDS = {
    "burst", "flooding", "flood", "sewage", "spraying",
    "overflow", "no water", "water everywhere", "water damage",
}


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def _elapsed(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)

def _safe_merge(state: PlumbingState, field: str, new_val) -> None:
    if new_val is not None and field_missing(state, field):
        state[field] = new_val

def _is_emergency(state: PlumbingState) -> bool:
    """Fast-path emergency detection — no LLM tokens."""
    issue = (state.get("issue") or "").lower()
    issue_type = state.get("issue_type", "")
    urgency = state.get("urgency") or state.get("ai_urgency", "")
    return (
        issue_type == "emergency"
        or urgency == "emergency"
        or any(kw in issue for kw in _EMERGENCY_KEYWORDS)
        or state.get("has_water_damage") and state.get("is_getting_worse")
    )


# ── 1. Validate ───────────────────────────────────────────────────────────────

async def node_validate_input(state: PlumbingState) -> PlumbingState:
    start = time.perf_counter()
    state["last_node"] = "validate_input"
    state["error"] = None

    msgs = state.get("messages", [])
    if not msgs:
        state["error"] = "empty_input"
        state["duration_ms"] = _elapsed(start)
        return state

    last = msgs[-1]
    if last.get("role") != "user" or not (last.get("content") or "").strip():
        state["error"] = "empty_input"
        state["duration_ms"] = _elapsed(start)
        return state

    if int(state.get("turn_count", 0)) >= _MAX_TURNS:
        state["is_complete"] = True
        logger.warning("session_max_turns_reached", session_id=state.get("session_id"))

    state["duration_ms"] = _elapsed(start)
    return state


# ── 2. Enrich ─────────────────────────────────────────────────────────────────

async def node_enrich_lead(state: PlumbingState) -> PlumbingState:
    start = time.perf_counter()
    state["last_node"] = "enrich_lead"

    messages = state.get("messages", [])
    last_user = next(
        (m["content"] for m in reversed(messages) if m.get("role") == "user"), None
    )

    # A. Extract plumbing fields from last user message only
    if last_user:
        try:
            extraction = await ai_tools.extract_plumbing_fields(last_user)
            if extraction:
                _safe_merge(state, "name",             extraction.get("name"))
                _safe_merge(state, "email",            extraction.get("email"))
                _safe_merge(state, "phone",            extraction.get("phone"))
                _safe_merge(state, "issue",            extraction.get("issue"))
                _safe_merge(state, "issue_type",       extraction.get("issue_type"))
                _safe_merge(state, "problem_area",     extraction.get("problem_area"))
                _safe_merge(state, "property_type",    extraction.get("property_type"))
                _safe_merge(state, "is_homeowner",     extraction.get("is_homeowner"))
                _safe_merge(state, "main_shutoff_off", extraction.get("main_shutoff_off"))
                addr = extraction.get("address") or extraction.get("location")
                _safe_merge(state, "address", addr)
                # Booleans — only set if explicitly stated
                for bf in ("has_water_damage", "is_getting_worse"):
                    if extraction.get(bf) is not None:
                        _safe_merge(state, bf, extraction[bf])
                # urgency — explicit only
                if extraction.get("urgency") and field_missing(state, "urgency"):
                    state["urgency"] = extraction["urgency"]
        except Exception as exc:
            logger.warning("plumbing_extraction_failed", error=str(exc),
                           session_id=state.get("session_id"))

    # B. Classify full history
    try:
        classification = await ai_tools.classify_conversation(messages)
        if classification:
            state["intent"]     = classification.get("intent", "service_request")
            state["is_spam"]    = classification.get("is_spam", False)
            state["ai_summary"] = classification.get("summary")
            state["ai_urgency"] = classification.get("urgency", "normal")
            # Promote ai_urgency → urgency after 2+ turns if unset
            if field_missing(state, "urgency") and int(state.get("turn_count", 0)) >= 2:
                state["urgency"] = state["ai_urgency"]
    except Exception as exc:
        logger.warning("classification_failed", error=str(exc),
                       session_id=state.get("session_id"))
        state.setdefault("is_spam", False)
        state.setdefault("intent", "service_request")

    # Fast-path: auto-set issue_type=emergency from keywords
    if field_missing(state, "issue_type") and _is_emergency(state):
        state["issue_type"] = "emergency"

    logger.info("plumbing_enriched",
        session_id=state.get("session_id"),
        collected={f: state.get(f) for f in _REQUIRED_FIELDS},
        issue_type=state.get("issue_type"),
        is_emergency=_is_emergency(state),
    )
    state["duration_ms"] = _elapsed(start)
    return state


# ── 3. Check completion ───────────────────────────────────────────────────────

node_check_completion = build_check_completion_node(_REQUIRED_FIELDS)


# ── 4. Chat reply ─────────────────────────────────────────────────────────────

node_chat_reply = build_chat_reply_node(PLUMBING_EXPERT_SYSTEM, _COLLECTED_FIELDS)


# ── 5. Score ──────────────────────────────────────────────────────────────────

async def node_score_lead(state: PlumbingState) -> PlumbingState:
    start = time.perf_counter()
    state["last_node"] = "score_lead"

    # Emergency fast-path — no LLM call needed
    if _is_emergency(state):
        state["score"]        = "hot"
        state["score_reason"] = "Emergency plumbing — immediate dispatch."
        state["next_step"]    = "immediate_dispatch"
        state["duration_ms"]  = _elapsed(start)
        return state

    urgency = state.get("urgency") or state.get("ai_urgency", "normal")
    urgency_map = {"emergency": "emergency", "urgent": "high", "routine": "normal", "normal": "normal"}
    mapped = urgency_map.get(urgency, "normal")

    snapshot = LeadEnrichment(
        name=state.get("name"),
        email=state.get("email"),
        phone=state.get("phone"),
        issue=state.get("issue"),
        urgency=mapped,
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
        logger.error("plumbing_score_failed", error=str(exc),
                     session_id=state.get("session_id"))
        state["score"]        = "warm"
        state["score_reason"] = "Scoring failed — defaulted to warm."
        state["next_step"]    = "schedule_callback"

    state["duration_ms"] = _elapsed(start)
    return state


# ── 6. Deliver ────────────────────────────────────────────────────────────────

async def node_finalize_and_deliver(state: PlumbingState) -> PlumbingState:
    """DB → Sheets → Email → WhatsApp (+ emergency SMS) via delivery pipeline."""
    start = time.perf_counter()
    state["last_node"] = "delivery"

    if state.get("is_spam") or state.get("next_step") == "drop":
        logger.info("plumbing_delivery_skipped", session_id=state.get("session_id"))
        state["duration_ms"] = _elapsed(start)
        return state

    # 1. DB persistence
    try:
        async with get_db_context() as db:
            lead = Lead(
                name=state.get("name"),
                email=state.get("email"),
                phone=state.get("phone"),
                issue=state.get("issue"),
                address=state.get("address"),
                vertical="plumbing",
                session_id=state.get("session_id"),
                score=state.get("score"),
                summary=state.get("ai_summary"),
            )
            db.add(lead)
            await db.commit()
            logger.info("plumbing_lead_persisted", session_id=state.get("session_id"))
    except Exception as exc:
        logger.error("plumbing_db_failed", error=str(exc),
                     session_id=state.get("session_id"))

    # 2. Sheets + Email + WhatsApp
    try:
        from tools.delivery_tools import run_delivery_pipeline
            
        return Command(
            goto="end",
            update={"is_complete": True}
        )

    except Exception as exc:
        logger.error(
            "hand_off_failed",
            session_id=state.get("session_id"),
            error=str(exc),
        )
        if "messages" in state and state["messages"]:
            # Basic fallback notification if hand-off crashes hard
            from tools.whatsapp_tools import whatsapp_tools
            # Reuse WhatsApp service but send as SMS (same Twilio client)
            from core.config import settings
            from twilio.rest import Client
            import asyncio
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            sms_body = (
                f"Sorry, I'm having trouble connecting you. "
                f"Please call us directly at {settings.PLUMBER_PHONE_NUMBER}."
            )
            # Attempt to send SMS to the user
            try:
                to_number = state["phone"] if state["phone"].startswith("+") else f"+{state['phone']}"
                await asyncio.to_thread(
                    client.messages.create,
                    from_=settings.TWILIO_FROM_NUMBER,
                    to=to_number,
                    body=sms_body,
                )
                logger.info("hand_off_fallback_sms_sent", session_id=state.get("session_id"))
            except Exception as sms_exc:
                logger.error("hand_off_fallback_sms_failed", error=str(sms_exc),
                             session_id=state.get("session_id"))

    # 3. Emergency SMS — additional to WhatsApp, sent via Twilio SMS
    if _is_emergency(state) and state.get("phone"):
        try:
            from tools.whatsapp_tools import whatsapp_tools
            # Reuse WhatsApp service but send as SMS (same Twilio client)
            from core.config import settings
            from twilio.rest import Client
            import asyncio
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            sms_body = (
                f"Emergency plumber dispatched to {state.get('address', 'your location')}. "
                "Keep main shutoff CLOSED. Tech calls in 15 min."
            )
            await asyncio.to_thread(
                client.messages.create,
                from_=settings.TWILIO_FROM_NUMBER,
                to=state["phone"] if state["phone"].startswith("+") else f"+{state['phone']}",
                body=sms_body,
            )
            logger.info("emergency_sms_sent", session_id=state.get("session_id"))
        except Exception as exc:
            logger.error("emergency_sms_failed", error=str(exc),
                         session_id=state.get("session_id"))

    state["duration_ms"] = _elapsed(start)
    return state