# workflows/roofing/nodes.py
from __future__ import annotations

import time
from datetime import datetime, timezone

import structlog
from langchain_core.messages import SystemMessage

from core.database import Lead, get_db_context
from llm import llm
from tools.ai_tools import ai_tools
from workflows.base import build_lc_messages, field_missing, get_appt_slots
from workflows.hvac.schema import LeadEnrichment, LeadScore
from workflows.roofing.prompts import ROOFING_EXPERT_SYSTEM
from workflows.roofing.state import RoofingState

logger = structlog.get_logger(__name__)

_MAX_TURNS = 10

_COLLECTED_FIELDS = (
    "damage_type", "damage_detail", "storm_date", "roof_age",
    "has_interior_leak", "has_insurance", "insurance_contacted",
    "adjuster_involved", "is_homeowner", "property_type",
    "address", "urgency", "name", "phone", "email",
)

# Minimum required: damage_type tells us storm vs wear (determines entire sales path),
# address allows us to dispatch inspector.
# name/phone/email pre-filled from form.
_REQUIRED_FIELDS = ("damage_type", "address")

# Storm signals for fast-path detection
_STORM_KEYWORDS = {
    "hail", "hailstorm", "storm", "wind damage", "tree fell",
    "missing shingles", "granules", "adjuster", "insurance claim",
    "neighbor filed",
}


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def _elapsed(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)

def _safe_merge(state: RoofingState, field: str, new_val) -> None:
    if new_val is not None and field_missing(state, field):
        state[field] = new_val

def _is_storm_lead(state: RoofingState) -> bool:
    """Fast-path storm detection — no LLM tokens."""
    damage = (state.get("damage_type") or "").lower()
    detail = (state.get("damage_detail") or "").lower()
    urgency = (state.get("urgency") or state.get("ai_urgency") or "").lower()
    return (
        damage == "storm"
        or urgency == "storm_damage"
        or state.get("adjuster_involved")
        or state.get("insurance_contacted")
        or any(kw in detail for kw in _STORM_KEYWORDS)
    )

def _is_high_value(state: RoofingState) -> bool:
    """Storm + insurance + homeowner = highest value lead."""
    return (
        _is_storm_lead(state)
        and state.get("has_insurance")
        and state.get("is_homeowner") is not False
    )


# ── 1. Validate ───────────────────────────────────────────────────────────────

async def node_validate_input(state: RoofingState) -> RoofingState:
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

async def node_enrich_lead(state: RoofingState) -> RoofingState:
    start = time.perf_counter()
    state["last_node"] = "enrich_lead"

    messages = state.get("messages", [])
    last_user = next(
        (m["content"] for m in reversed(messages) if m.get("role") == "user"), None
    )

    # A. Extract roofing fields from last user message only
    if last_user:
        try:
            extraction = await ai_tools.extract_roofing_fields(last_user)
            if extraction:
                _safe_merge(state, "name",   extraction.get("name"))
                _safe_merge(state, "email",  extraction.get("email"))
                _safe_merge(state, "phone",  extraction.get("phone"))
                _safe_merge(state, "damage_type",   extraction.get("damage_type"))
                _safe_merge(state, "damage_detail",  extraction.get("damage_detail"))
                _safe_merge(state, "storm_date",     extraction.get("storm_date"))
                _safe_merge(state, "roof_age",       extraction.get("roof_age"))
                _safe_merge(state, "property_type",  extraction.get("property_type"))
                _safe_merge(state, "is_homeowner",   extraction.get("is_homeowner"))
                addr = extraction.get("address") or extraction.get("location")
                _safe_merge(state, "address", addr)
                # Boolean flags — allow update (insurance status can change)
                for bf in ("has_insurance", "insurance_contacted",
                           "adjuster_involved", "has_interior_leak"):
                    if extraction.get(bf) is not None:
                        _safe_merge(state, bf, extraction[bf])
                if extraction.get("urgency") and field_missing(state, "urgency"):
                    state["urgency"] = extraction["urgency"]
        except Exception as exc:
            logger.warning("roofing_extraction_failed", error=str(exc),
                           session_id=state.get("session_id"))

    # B. Classify full history
    try:
        classification = await ai_tools.classify_conversation(messages)
        if classification:
            state["intent"]     = classification.get("intent", "service_request")
            state["is_spam"]    = classification.get("is_spam", False)
            state["ai_summary"] = classification.get("summary")
            state["ai_urgency"] = classification.get("urgency", "normal")
            if field_missing(state, "urgency") and int(state.get("turn_count", 0)) >= 2:
                state["urgency"] = state["ai_urgency"]
    except Exception as exc:
        logger.warning("classification_failed", error=str(exc),
                       session_id=state.get("session_id"))
        state.setdefault("is_spam", False)
        state.setdefault("intent", "service_request")

    logger.info("roofing_enriched",
        session_id=state.get("session_id"),
        collected={f: state.get(f) for f in _REQUIRED_FIELDS},
        is_storm=_is_storm_lead(state),
        is_high_value=_is_high_value(state),
    )
    state["duration_ms"] = _elapsed(start)
    return state


# ── 3. Check completion ───────────────────────────────────────────────────────

async def node_check_completion(state: RoofingState) -> RoofingState:
    if state.get("is_complete"):
        return state
    if all(not field_missing(state, f) for f in _REQUIRED_FIELDS):
        state["is_complete"] = True
    return state


# ── 4. Chat reply ─────────────────────────────────────────────────────────────

async def node_chat_reply(state: RoofingState) -> RoofingState:
    start = time.perf_counter()
    state["last_node"] = "chat_reply"

    # Completion turn — farewell varies by lead type
    if state.get("is_complete"):
        address  = state.get("address") or "your property"
        phone    = state.get("phone")   or "the number you provided"
        is_storm = _is_storm_lead(state)
        is_hv    = _is_high_value(state)

        if is_hv:
            # Storm + insurance — highest value path
            reply_content = (
                f"Perfect — scheduling a free inspection at {address}. "
                f"Our inspector will document everything with photos for your insurance claim. "
                f"They'll call {phone} 30 minutes before arrival. You're all set!"
            )
        elif is_storm:
            # Storm but no insurance confirmed yet
            reply_content = (
                f"Scheduling a free inspection at {address} for storm damage assessment. "
                f"Our inspector will call {phone} 30 minutes before arrival with a photo report. "
                "If you have homeowners insurance, have your policy number handy."
            )
        else:
            # Wear / routine
            reply_content = (
                f"Scheduling a free inspection at {address}. "
                f"Our inspector will assess the damage and walk you through options. "
                f"They'll call {phone} 30 minutes before arrival. You're all set!"
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
    expert_prompt = ROOFING_EXPERT_SYSTEM.format(
        collected=str(collected),
        slot_1=slots[0],
        slot_2=slots[1],
        slot_3=slots[2],
    )
    messages_lc = [SystemMessage(content=expert_prompt)] + build_lc_messages(state)

    logger.debug("roofing_chat_reply_invoke",
        session_id=state.get("session_id"),
        turn=state.get("turn_count", 0),
        collected_fields=list(collected.keys()),
        is_storm=_is_storm_lead(state),
    )

    try:
        resp = await llm.ainvoke(messages_lc)
        reply_content = resp.content
        state["turn_count"] = int(state.get("turn_count", 0)) + 1
    except Exception as exc:
        logger.error("roofing_chat_reply_failed", error=str(exc),
                     session_id=state.get("session_id"))
        state["error"] = "llm_failure"
        reply_content = "Sorry, I had a hiccup. Could you repeat that?"

    existing = list(state.get("messages", []))
    existing.append({"role": "assistant", "content": reply_content, "ts": _utcnow()})
    state["messages"] = existing
    state["duration_ms"] = _elapsed(start)
    return state


# ── 5. Score ──────────────────────────────────────────────────────────────────

async def node_score_lead(state: RoofingState) -> RoofingState:
    start = time.perf_counter()
    state["last_node"] = "score_lead"

    # Fast-path: storm + insurance + homeowner = always hot
    if _is_high_value(state):
        bonus = " Adjuster involved." if state.get("adjuster_involved") else ""
        state["score"]        = "hot"
        state["score_reason"] = f"Storm damage + insurance + homeowner.{bonus}"
        state["next_step"]    = "immediate_dispatch"
        state["duration_ms"]  = _elapsed(start)
        return state

    # Fast-path: storm without insurance = warm (still high priority)
    if _is_storm_lead(state) and not state.get("has_insurance"):
        state["score"]        = "warm"
        state["score_reason"] = "Storm damage, insurance status unknown."
        state["next_step"]    = "schedule_callback"
        state["duration_ms"]  = _elapsed(start)
        return state

    # LLM scoring for wear/routine leads
    urgency_map = {
        "storm_damage": "emergency", "leak_active": "high",
        "inspection_needed": "normal", "planning": "low",
    }
    urgency = state.get("urgency") or state.get("ai_urgency", "planning")
    mapped = urgency_map.get(urgency, "normal")

    snapshot = LeadEnrichment(
        name=state.get("name"),
        email=state.get("email"),
        phone=state.get("phone"),
        issue=state.get("damage_type") or "roofing inquiry",
        urgency=mapped,
        intent=state.get("intent", "service_request"),
        is_spam=state.get("is_spam", False),
        summary=state.get("ai_summary") or "Roofing lead",
    )

    try:
        score_data: LeadScore = await ai_tools.score_lead(snapshot)
        state["score"]        = score_data.score
        state["score_reason"] = score_data.score_reason
        state["next_step"]    = score_data.next_step
    except Exception as exc:
        logger.error("roofing_score_failed", error=str(exc),
                     session_id=state.get("session_id"))
        state["score"]        = "warm"
        state["score_reason"] = "Scoring failed — defaulted to warm."
        state["next_step"]    = "schedule_callback"

    state["duration_ms"] = _elapsed(start)
    return state


# ── 6. Deliver ────────────────────────────────────────────────────────────────

async def node_finalize_and_deliver(state: RoofingState) -> RoofingState:
    """DB → Sheets → Email → WhatsApp (+ insurance SMS reminder for storm leads)."""
    start = time.perf_counter()
    state["last_node"] = "delivery"

    if state.get("is_spam") or state.get("next_step") == "drop":
        logger.info("roofing_delivery_skipped", session_id=state.get("session_id"))
        state["duration_ms"] = _elapsed(start)
        return state

    # 1. DB persistence
    try:
        async with get_db_context() as db:
            lead = Lead(
                name=state.get("name"),
                email=state.get("email"),
                phone=state.get("phone"),
                issue=state.get("damage_type") or "roofing inquiry",
                address=state.get("address"),
                vertical="roofing",
                session_id=state.get("session_id"),
                score=state.get("score"),
                summary=state.get("ai_summary"),
            )
            db.add(lead)
            await db.commit()
            logger.info("roofing_lead_persisted", session_id=state.get("session_id"))
    except Exception as exc:
        logger.error("roofing_db_failed", error=str(exc),
                     session_id=state.get("session_id"))

    # 2. Sheets + Email + WhatsApp
    try:
        from tools.delivery_tools import run_delivery_pipeline
        results = await run_delivery_pipeline(state)
        state["delivery_results"] = results
    except Exception as exc:
        logger.error("roofing_delivery_pipeline_failed", error=str(exc),
                     session_id=state.get("session_id"))

    # 3. Insurance reminder SMS — storm leads with insurance confirmed
    if _is_storm_lead(state) and state.get("has_insurance") and state.get("phone"):
        try:
            from core.config import settings
            from twilio.rest import Client
            import asyncio
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            name = state.get("name") or "there"
            phone = state["phone"]
            if not phone.startswith("+"):
                phone = f"+{phone}"
            sms = (
                f"Hi {name}! Roof inspection coming up. "
                "Have your homeowners insurance policy number handy — "
                "our inspector will help with the claims process."
            )
            await asyncio.to_thread(
                client.messages.create,
                from_=settings.TWILIO_FROM_NUMBER,
                to=phone,
                body=sms,
            )
            logger.info("insurance_reminder_sms_sent", session_id=state.get("session_id"))
        except Exception as exc:
            logger.error("insurance_reminder_sms_failed", error=str(exc),
                         session_id=state.get("session_id"))

    state["duration_ms"] = _elapsed(start)
    return state