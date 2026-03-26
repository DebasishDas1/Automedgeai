# workflows/pest_control/nodes.py
from __future__ import annotations

import time
from datetime import datetime, timezone

import structlog
from langchain_core.messages import SystemMessage

from core.database import Lead, get_db_context
from llm import llm
from tools.ai_tools import ai_tools
from workflows.base import build_lc_messages, field_missing, get_appt_slots
from workflows.hvac.schema import LeadEnrichment, LeadScore  # reuse shared schemas
from workflows.pest_control.prompts import PEST_EXPERT_SYSTEM
from workflows.pest_control.state import PestState

logger = structlog.get_logger(__name__)

_MAX_TURNS = 10

# Fields shown to LLM as collected context
_COLLECTED_FIELDS = (
    "pest_type", "infestation_area", "duration", "has_damage",
    "tried_treatment", "is_homeowner", "property_type", "address",
    "urgency", "wants_annual", "name", "phone", "email",
)

# Fields required before is_complete fires.
# name/phone/email come from the lead form — not required here.
# Bot collects pest_type + address, urgency is promoted from ai_urgency.
_REQUIRED_FIELDS = ("pest_type", "address")


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def _elapsed(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)

def _safe_merge(state: PestState, field: str, new_val) -> None:
    """Only write if field not already captured."""
    if new_val is not None and field_missing(state, field):
        state[field] = new_val


# ── 1. Validate ───────────────────────────────────────────────────────────────

async def node_validate_input(state: PestState) -> PestState:
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

async def node_enrich_lead(state: PestState) -> PestState:
    start = time.perf_counter()
    state["last_node"] = "enrich_lead"

    messages = state.get("messages", [])
    last_user = next(
        (m["content"] for m in reversed(messages) if m.get("role") == "user"), None
    )

    # A. Extract pest-specific fields from last user message
    if last_user:
        try:
            extraction = await ai_tools.extract_pest_fields(last_user)
            if extraction:
                # Contact fields (usually from form, but catch if stated in chat)
                _safe_merge(state, "name",  extraction.get("name"))
                _safe_merge(state, "email", extraction.get("email"))
                _safe_merge(state, "phone", extraction.get("phone"))
                # Pest-specific fields — safe merge so first capture wins
                _safe_merge(state, "pest_type",        extraction.get("pest_type"))
                _safe_merge(state, "infestation_area", extraction.get("infestation_area"))
                _safe_merge(state, "duration",         extraction.get("duration"))
                _safe_merge(state, "property_type",    extraction.get("property_type"))
                addr = extraction.get("address") or extraction.get("location")
                _safe_merge(state, "address", addr)
                # Boolean fields — only set if explicitly stated
                for bool_field in ("has_damage", "tried_treatment", "is_homeowner", "wants_annual"):
                    val = extraction.get(bool_field)
                    if val is not None:
                        _safe_merge(state, bool_field, val)
                # Urgency from extraction — only if explicit
                if extraction.get("urgency") and field_missing(state, "urgency"):
                    state["urgency"] = extraction["urgency"]
        except Exception as exc:
            logger.warning("pest_extraction_failed", error=str(exc),
                           session_id=state.get("session_id"))

    # B. Classify full history for assessment fields
    try:
        classification = await ai_tools.classify_conversation(messages)
        if classification:
            state["intent"]     = classification.get("intent", "service_request")
            state["is_spam"]    = classification.get("is_spam", False)
            state["ai_summary"] = classification.get("summary")
            state["ai_urgency"] = classification.get("urgency", "normal")
            # Promote after 2+ turns if urgency not explicitly stated
            if field_missing(state, "urgency") and int(state.get("turn_count", 0)) >= 2:
                state["urgency"] = state["ai_urgency"]
    except Exception as exc:
        logger.warning("classification_failed", error=str(exc),
                       session_id=state.get("session_id"))
        state.setdefault("is_spam", False)
        state.setdefault("intent", "service_request")

    logger.info("pest_enriched",
        session_id=state.get("session_id"),
        collected={f: state.get(f) for f in _REQUIRED_FIELDS},
        pest_type=state.get("pest_type"),
    )
    state["duration_ms"] = _elapsed(start)
    return state


# ── 3. Check completion ───────────────────────────────────────────────────────

async def node_check_completion(state: PestState) -> PestState:
    if state.get("is_complete"):
        return state
    if all(not field_missing(state, f) for f in _REQUIRED_FIELDS):
        state["is_complete"] = True
    return state


# ── 4. Chat reply ─────────────────────────────────────────────────────────────

async def node_chat_reply(state: PestState) -> PestState:
    start = time.perf_counter()
    state["last_node"] = "chat_reply"

    # Completion turn — deterministic farewell, no LLM call
    if state.get("is_complete"):
        pest    = state.get("pest_type") or "your pest issue"
        address = state.get("address") or "your location"
        phone   = state.get("phone") or "the number you provided"
        reply_content = (
            f"Perfect — scheduling a free inspection at {address} for {pest}. "
            f"Our specialist will call {phone} to confirm the time. You're all set!"
        )
        state["turn_count"] = int(state.get("turn_count", 0)) + 1
        existing = list(state.get("messages", []))
        existing.append({"role": "assistant", "content": reply_content, "ts": _utcnow()})
        state["messages"] = existing
        state["duration_ms"] = _elapsed(start)
        return state

    # Normal turn — LLM asks next diagnostic question
    slots = state.get("appt_slots") or get_appt_slots()
    state["appt_slots"] = slots

    collected = {f: state.get(f) for f in _COLLECTED_FIELDS if state.get(f) is not None}
    expert_prompt = PEST_EXPERT_SYSTEM.format(
        collected=str(collected),
        slot_1=slots[0],
        slot_2=slots[1],
        slot_3=slots[2],
    )
    messages_lc = [SystemMessage(content=expert_prompt)] + build_lc_messages(state)

    logger.debug("pest_chat_reply_invoke",
        session_id=state.get("session_id"),
        turn=state.get("turn_count", 0),
        collected_fields=list(collected.keys()),
    )

    try:
        resp = await llm.ainvoke(messages_lc)
        reply_content = resp.content
        state["turn_count"] = int(state.get("turn_count", 0)) + 1
    except Exception as exc:
        logger.error("pest_chat_reply_failed", error=str(exc),
                     session_id=state.get("session_id"))
        state["error"] = "llm_failure"
        reply_content = "Sorry, I had a hiccup. Could you repeat that?"

    existing = list(state.get("messages", []))
    existing.append({"role": "assistant", "content": reply_content, "ts": _utcnow()})
    state["messages"] = existing
    state["duration_ms"] = _elapsed(start)
    return state


# ── 5. Score ──────────────────────────────────────────────────────────────────

async def node_score_lead(state: PestState) -> PestState:
    start = time.perf_counter()
    state["last_node"] = "score_lead"

    urgency = state.get("urgency") or state.get("ai_urgency", "normal")
    # Map pest urgency levels to LeadEnrichment urgency literals
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
        from tools.ai_tools import ai_tools as _ai
        score_data: LeadScore = await _ai.score_lead(snapshot)
        state["score"]        = score_data.score
        state["score_reason"] = score_data.score_reason
        state["next_step"]    = score_data.next_step
    except Exception as exc:
        logger.error("pest_score_failed", error=str(exc), session_id=state.get("session_id"))
        state["score"]        = "warm"
        state["score_reason"] = "Scoring failed — defaulted to warm."
        state["next_step"]    = "schedule_callback"

    state["duration_ms"] = _elapsed(start)
    return state


# ── 6. Deliver ────────────────────────────────────────────────────────────────

async def node_finalize_and_deliver(state: PestState) -> PestState:
    """DB → Sheets → Email → WhatsApp via shared delivery pipeline."""
    start = time.perf_counter()
    state["last_node"] = "delivery"

    if state.get("is_spam") or state.get("next_step") == "drop":
        logger.info("pest_delivery_skipped", session_id=state.get("session_id"))
        state["duration_ms"] = _elapsed(start)
        return state

    # 1. DB persistence
    try:
        async with get_db_context() as db:
            lead = Lead(
                name=state.get("name"),
                email=state.get("email"),
                phone=state.get("phone"),
                issue=state.get("pest_type"),
                address=state.get("address"),
                vertical="pest_control",
                session_id=state.get("session_id"),
                score=state.get("score"),
                summary=state.get("ai_summary"),
            )
            db.add(lead)
            await db.commit()
            logger.info("pest_lead_persisted", session_id=state.get("session_id"))
    except Exception as exc:
        logger.error("pest_db_failed", error=str(exc), session_id=state.get("session_id"))

    # 2. Sheets + Email + WhatsApp
    try:
        from tools.delivery_tools import run_delivery_pipeline
        results = await run_delivery_pipeline(state)
        state["delivery_results"] = results
    except Exception as exc:
        logger.error("pest_delivery_pipeline_failed", error=str(exc),
                     session_id=state.get("session_id"))

    state["duration_ms"] = _elapsed(start)
    return state