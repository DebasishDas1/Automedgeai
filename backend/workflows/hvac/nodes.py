# workflows/hvac/nodes.py
from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone

import structlog
from langchain_core.messages import SystemMessage

from core.database import Lead, get_db_context
from llm import llm
from tools.ai_tools import ai_tools
from workflows.base import build_lc_messages, field_missing, get_appt_slots
from workflows.hvac.prompts import HVAC_EXPERT_SYSTEM
from workflows.hvac.schema import LeadEnrichment, LeadScore
from workflows.hvac.state import HvacState

logger = structlog.get_logger(__name__)

_MAX_TURNS        = 10
_COLLECTED_FIELDS = ("issue", "description", "urgency", "address", "name", "phone", "email")
_REQUIRED_FIELDS  = ("issue", "urgency", "address")


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def _elapsed(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)

def _safe_merge(state: HvacState, field: str, new_val) -> None:
    if new_val is not None and field_missing(state, field):
        state[field] = new_val

def _migrate_legacy_fields(state: HvacState) -> None:
    """Fix old sessions that used 'location' instead of 'address'."""
    if field_missing(state, "address") and state.get("location"):
        state["address"] = state.pop("location")
    # Promote ai_urgency → urgency after 2+ turns if still unset
    if field_missing(state, "urgency") and state.get("ai_urgency"):
        if int(state.get("turn_count", 0)) >= 2:
            state["urgency"] = state["ai_urgency"]
            logger.debug("urgency_promoted", urgency=state["urgency"],
                         session_id=state.get("session_id"))


# ── 1. Validate ───────────────────────────────────────────────────────────────

async def node_validate_input(state: HvacState) -> HvacState:
    start = time.perf_counter()
    state["last_node"] = "validate_input"
    state["error"] = None

    _migrate_legacy_fields(state)

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

async def node_enrich_lead(state: HvacState) -> HvacState:
    start = time.perf_counter()
    state["last_node"] = "enrich_lead"

    messages = state.get("messages", [])
    last_user = next(
        (m["content"] for m in reversed(messages) if m.get("role") == "user"), None
    )

    # A. Extract contact fields from last user message only
    if last_user:
        try:
            extraction = await ai_tools.extract_fields(last_user)
            if extraction:
                _safe_merge(state, "name",         extraction.get("name"))
                _safe_merge(state, "email",        extraction.get("email"))
                _safe_merge(state, "phone",        extraction.get("phone"))
                _safe_merge(state, "issue",        extraction.get("issue"))
                _safe_merge(state, "description",  extraction.get("description"))
                _safe_merge(state, "is_homeowner", extraction.get("is_homeowner"))
                addr = extraction.get("address") or extraction.get("location")
                _safe_merge(state, "address", addr)
                extracted_urgency = extraction.get("urgency")
                if extracted_urgency and field_missing(state, "urgency"):
                    state["urgency"] = extracted_urgency
        except Exception as exc:
            logger.warning("field_extraction_failed", error=str(exc),
                           session_id=state.get("session_id"))

    # B. Classify full history — assessment only, not a collected field
    try:
        classification = await ai_tools.classify_conversation(messages)
        if classification:
            state["intent"]     = classification.get("intent", "service_request")
            state["is_spam"]    = classification.get("is_spam", False)
            state["ai_summary"] = classification.get("summary")
            state["ai_urgency"] = classification.get("urgency", "normal")
            # Promote ai_urgency after 2+ turns if still unset
            if field_missing(state, "urgency") and int(state.get("turn_count", 0)) >= 2:
                state["urgency"] = state["ai_urgency"]
                logger.debug("urgency_promoted", urgency=state["urgency"],
                             session_id=state.get("session_id"))
    except Exception as exc:
        logger.warning("classification_failed", error=str(exc),
                       session_id=state.get("session_id"))
        state.setdefault("is_spam", False)
        state.setdefault("intent", "service_request")

    logger.info("lead_enriched",
        session_id=state.get("session_id"),
        collected={f: state.get(f) for f in _REQUIRED_FIELDS},
    )
    state["duration_ms"] = _elapsed(start)
    return state


# ── 3. Check completion ───────────────────────────────────────────────────────

async def node_check_completion(state: HvacState) -> HvacState:
    if state.get("is_complete"):
        return state
    if all(not field_missing(state, f) for f in _REQUIRED_FIELDS):
        state["is_complete"] = True
    return state


# ── 4. Chat reply ─────────────────────────────────────────────────────────────

async def node_chat_reply(state: HvacState) -> HvacState:
    start = time.perf_counter()
    state["last_node"] = "chat_reply"

    # Completion turn — deterministic farewell, no LLM call
    if state.get("is_complete"):
        address = state.get("address") or "your location"
        issue   = state.get("issue")   or "your issue"
        phone   = state.get("phone")   or "the number you provided"
        reply_content = (
            f"Perfect — dispatching a technician to {address} for {issue}. "
            f"Our tech will call {phone} within 15 minutes. You're all set!"
        )
        state["turn_count"] = int(state.get("turn_count", 0)) + 1
        existing = list(state.get("messages", []))
        existing.append({"role": "assistant", "content": reply_content, "ts": _utcnow()})
        state["messages"] = existing
        state["duration_ms"] = _elapsed(start)
        return state

    # Normal turn — LLM asks for next missing field
    slots = state.get("appt_slots") or get_appt_slots()
    state["appt_slots"] = slots

    collected = {f: state.get(f) for f in _COLLECTED_FIELDS if state.get(f) is not None}
    expert_prompt = HVAC_EXPERT_SYSTEM.format(collected=str(collected))
    messages_lc = [SystemMessage(content=expert_prompt)] + build_lc_messages(state)

    logger.debug("chat_reply_invoke",
        session_id=state.get("session_id"),
        turn=state.get("turn_count", 0),
        collected_fields=list(collected.keys()),
        history_len=len(messages_lc),
    )

    try:
        resp = await llm.ainvoke(messages_lc)
        reply_content = resp.content
        state["turn_count"] = int(state.get("turn_count", 0)) + 1
    except Exception as exc:
        logger.error("chat_reply_failed", error=str(exc), session_id=state.get("session_id"))
        state["error"] = "llm_failure"
        reply_content = "Sorry, I had a hiccup. Could you repeat that?"

    existing = list(state.get("messages", []))
    existing.append({"role": "assistant", "content": reply_content, "ts": _utcnow()})
    state["messages"] = existing
    state["duration_ms"] = _elapsed(start)
    return state


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
        logger.error("score_lead_failed", error=str(exc), session_id=state.get("session_id"))
        state["score"]        = "warm"
        state["score_reason"] = "Scoring failed — defaulted to warm."
        state["next_step"]    = "schedule_callback"

    state["duration_ms"] = _elapsed(start)
    return state


# ── 6. Deliver ────────────────────────────────────────────────────────────────

async def node_finalize_and_deliver(state: HvacState) -> HvacState:
    """
    Full delivery pipeline: DB → Sheets → Email → WhatsApp.
    Each step is isolated — failure in one never blocks the others.
    """
    start = time.perf_counter()
    state["last_node"] = "delivery"

    if state.get("is_spam") or state.get("next_step") == "drop":
        logger.info("delivery_skipped", session_id=state.get("session_id"))
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
                vertical=state.get("vertical", "hvac"),
                session_id=state.get("session_id"),
                score=state.get("score"),
                summary=state.get("ai_summary"),
            )
            db.add(lead)
            await db.commit()
            logger.info("lead_persisted", session_id=state.get("session_id"))
    except Exception as exc:
        logger.error("db_persistence_failed", error=str(exc),
                     session_id=state.get("session_id"))

    # 2. Sheets + Email + WhatsApp via delivery pipeline
    try:
        from tools.delivery_tools import run_delivery_pipeline
        results = await run_delivery_pipeline(state)
        state["delivery_results"] = results
    except Exception as exc:
        logger.error("delivery_pipeline_failed", error=str(exc),
                     session_id=state.get("session_id"))

    state["duration_ms"] = _elapsed(start)
    return state