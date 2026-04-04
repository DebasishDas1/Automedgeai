# workflows/shared.py
from __future__ import annotations

import json
import re
import time
from typing import Callable, Any

import structlog
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END

from llm import llm
from workflows.base import field_missing

logger = structlog.get_logger(__name__)


def _elapsed(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


def build_validate_input_node(_MAX_TURNS: int = 10, migrate_fn: Optional[Callable] = None) -> Callable:
    """
    Standard validation: checks for empty input and turn limits.
    Supports an optional migration function for legacy state fixes.
    """
    async def node_validate_input(state: dict) -> dict:
        start = time.perf_counter()
        state["last_node"] = "validate_input"
        state["error"] = None

        if migrate_fn:
            migrate_fn(state)

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
    return node_validate_input


def build_check_completion_node(required_fields: tuple[str, ...]) -> Callable:
    """
    Session completes when:
      1. All required fields are collected, AND
      2. One of:
         a. It's an emergency (dispatch immediately — no appointment hold)
         b. User explicitly doesn't want an appointment
         c. Appointment confirmed/booked
         d. wants_appointment=None and turn_count >= 2 (bot has had a chance to offer)

    FIX: previous version used turn_count >= 3, but turn_count is incremented
    by node_chat_reply AFTER check_done runs. So at turn 2 of conversation,
    turn_count in state is still 1 when check_done evaluates. This caused the
    bot to ask for info it already had. Changed to >= 2 which means "the reply
    node has run at least once since data collection completed."

    FIX: emergency leads bypass the appointment hold entirely — immediate dispatch.
    """
    async def node_check_completion(state: dict) -> dict:
        if state.get("is_complete"):
            return state

        # Required fields not yet collected
        if not all(not field_missing(state, f) for f in required_fields):
            return state

        # Emergency — complete immediately, no appointment hold
        issue_type = state.get("issue_type", "")
        urgency = state.get("urgency") or state.get("ai_urgency", "")
        is_emergency = (
            issue_type == "emergency"
            or urgency == "emergency"
            or urgency == "urgent"
            or state.get("_is_emergency_logic", False)  # Vertical-specific flag
        )
        if is_emergency:
            state["is_complete"] = True
            return state

        # Explicit no-appointment
        if state.get("wants_appointment") is False:
            state["is_complete"] = True
            return state

        # Appointment confirmed
        if state.get("appt_confirmed") or state.get("appt_booked"):
            state["is_complete"] = True
            return state

        # Waiting for user to confirm appointment — stay open
        if state.get("wants_appointment") is True:
            return state

        # wants_appointment=None: give reply node one chance to offer slots,
        # then complete on the next check. turn_count >= 2 means the reply
        # node has already run at least twice in this session.
        if int(state.get("turn_count", 0)) >= 2:
            state["is_complete"] = True

        return state
    return node_check_completion


def build_enrich_node(
    extract_fn: Callable,
    required_fields: tuple[str, ...],
    collected_fields: tuple[str, ...],
    is_emergency_fn: Optional[Callable] = None,
) -> Callable:
    """
    Standardized enrichment node builder.
    - Runs extraction and classification in parallel.
    - Automates field merging and location normalization.
    - Detects appointment intent.
    - Updates vertical-specific emergency flags.
    """
    async def node_enrich_lead(state: dict) -> dict:
        from tools.ai_tools import ai_tools
        import asyncio
        start = time.perf_counter()
        state["last_node"] = "enrich_lead"

        messages = state.get("messages", [])
        last_user = next(
            (m["content"] for m in reversed(messages) if m.get("role") == "user"), None
        )

        async def _noop(): return None

        extraction, classification = await asyncio.gather(
            extract_fn(last_user) if last_user else _noop(),
            ai_tools.classify_conversation(messages),
            return_exceptions=True,
        )

        # 1. Extraction Merge
        if isinstance(extraction, Exception):
            logger.warning("extraction_failed", error=str(extraction), sid=state.get("session_id"))
        elif extraction:
            for field, value in extraction.items():
                if value is None: continue
                if field == "location" and not extraction.get("address"):
                    state["address"] = value
                elif field in collected_fields:
                    state[field] = value

        # 2. Classification Merge
        if isinstance(classification, Exception):
            logger.warning("classification_failed", error=str(classification), sid=state.get("session_id"))
        elif classification:
            state["intent"]     = classification.get("intent", "service_request")
            state["is_spam"]    = classification.get("is_spam", False)
            state["ai_summary"] = classification.get("summary")
            state["ai_urgency"] = classification.get("urgency", "normal")
            if int(state.get("turn_count", 0)) >= 2:
                state["urgency"] = state["ai_urgency"]

        # 3. Vertical Logic (Emergency + Appt Intent)
        if is_emergency_fn:
            state["_is_emergency_logic"] = is_emergency_fn(state)
        
        if last_user and not state.get("wants_appointment"):
            appt_keywords = {"book", "schedule", "appointment", "appt", "slot", "tomorrow"}
            if any(kw in last_user.lower() for kw in appt_keywords):
                state["wants_appointment"] = True

        logger.info("enrich_complete", sid=state.get("session_id"),
                    req_met=all(not field_missing(state, f) for f in required_fields))
        state["duration_ms"] = _elapsed(start)
        return state

    return node_enrich_lead


def build_chat_reply_node(
    system_prompt_template: str,
    fields_to_collect: tuple[str, ...],
) -> Callable:
    """
    Chat reply node.
    - Formats collected fields + appointment slots into the system prompt.
    - Strips code fences from model output.
    - Detects appointment confirmation from the assistant's own reply text.
    """
    async def node_chat_reply(state: dict) -> dict:
        collected = {
            k: state.get(k)
            for k in fields_to_collect
            if state.get(k) is not None
        }

        try:
            system_prompt = system_prompt_template.format(
                collected=json.dumps(collected, ensure_ascii=False)
            )
        except KeyError:
            from workflows.base import get_appt_slots
            slots = state.get("appt_slots") or get_appt_slots()
            state["appt_slots"] = slots
            kwargs = {"collected": json.dumps(collected, ensure_ascii=False)}
            for i, slot in enumerate(slots[:3]):
                kwargs[f"slot_{i+1}"] = slot
            system_prompt = system_prompt_template.format(**kwargs)

        last_user = next(
            (m["content"] for m in reversed(state.get("messages", []))
             if m.get("role") == "user"),
            "",
        )

        # Standardize completion message if session is already complete.
        if state.get("is_complete"):
            # Check if we've already acknowledged the recording in the conversation
            already_acknowledged = any(
                "recorded" in m.get("content", "").lower()
                for m in reversed(state.get("messages", []))
                if m.get("role") == "assistant"
            )
            if not already_acknowledged:
                completion_instr = (
                    "\n\nSESSION IS COMPLETE. Respond with a short, professional closing. "
                    "Include: 'Your interaction is recorded', 'Let's schedule a service', and "
                    "'Let us know what more we can help with' (or natural variations)."
                )
            else:
                completion_instr = (
                    "\n\nSession remains complete. Briefly offer further assistance "
                    "('Let us know what more we can help with') without repeating the recorded interaction."
                )
            system_prompt += completion_instr

        from workflows.base import build_lc_messages
        history = build_lc_messages(state)

        reply = await llm.ainvoke(
            [SystemMessage(content=system_prompt)] + history,
            session_id=state.get("session_id", "global")
        )

        assistant_text = reply.content.strip()
        # Strip any code fences the model might emit
        assistant_text = re.sub(r"^```[a-z]*\n?", "", assistant_text).strip()
        assistant_text = re.sub(r"```$", "", assistant_text).strip()

        new_messages = list(state.get("messages", []))
        new_messages.append({"role": "assistant", "content": assistant_text})

        updated = {
            **state,
            "messages":   new_messages,
            "turn_count": state.get("turn_count", 0) + 1,
            "last_node":  "reply",
        }

        # Detect appointment confirmation from assistant reply
        if not updated.get("appt_booked") and not updated.get("appt_confirmed"):
            appt_slots = updated.get("appt_slots") or []
            reply_lower = assistant_text.lower()
            for slot in appt_slots:
                if slot.lower() in reply_lower or "you're all set" in reply_lower or "you're booked" in reply_lower:
                    updated["appt_booked"]    = True
                    updated["appt_confirmed"] = slot
                    logger.info("appointment_confirmed_from_reply",
                                session_id=updated.get("session_id"), slot=slot)
                    break

        return updated
    return node_chat_reply


def _route_completion(state: dict) -> str:
    return "complete" if state.get("is_complete") else "continue"


def _route_post_score(state: dict) -> str:
    if state.get("is_spam") or state.get("next_step") == "drop":
        return "skip"
    return "go"


def build_chat_graph(state_schema: Any, nodes_dict: dict, always_reply: bool = True) -> Callable:
    def builder():
        g = StateGraph(state_schema)
        g.add_node("validate",   nodes_dict["validate"])
        g.add_node("enrich",     nodes_dict["enrich"])
        g.add_node("check_done", nodes_dict["check_done"])
        g.add_node("reply",      nodes_dict["reply"])
        g.set_entry_point("validate")
        g.add_edge("validate",   "enrich")
        g.add_edge("enrich",     "check_done")
        edges = (
            {"complete": "reply", "continue": "reply"}
            if always_reply
            else {"complete": END, "continue": "reply"}
        )
        g.add_conditional_edges("check_done", _route_completion, edges)
        g.add_edge("reply", END)
        return g.compile()
    return builder


def build_delivery_node(vertical: str, emergency_sms_fn: Optional[Callable] = None) -> Callable:
    """
    Standardized delivery node builder.
    - DB persistence.
    - Delivery pipeline (Sheets, Email, WhatsApp, HubSpot).
    - Optional emergency SMS trigger.
    """
    async def node_finalize_and_deliver(state: dict) -> dict:
        from core.database import Lead, get_db_context
        from tools.delivery_tools import run_delivery_pipeline
        start = time.perf_counter()
        state["last_node"] = "delivery"

        if state.get("is_spam") or state.get("next_step") == "drop":
            logger.info("delivery_skipped", sid=state.get("session_id"))
            return state

        # 1. DB
        try:
            async with get_db_context() as db:
                lead = Lead(
                    name=state.get("name"), email=state.get("email"),
                    phone=state.get("phone"), issue=state.get("issue"),
                    address=state.get("address"), vertical=vertical,
                    session_id=state.get("session_id"), score=state.get("score"),
                    summary=state.get("ai_summary"),
                )
                db.add(lead)
                await db.commit()
                logger.info("db_persisted", sid=state.get("session_id"))
        except Exception as exc:
            logger.error("db_failed", error=str(exc), sid=state.get("session_id"))

        # 2. Pipeline
        try:
            await run_delivery_pipeline(state)
            logger.info("delivery_pipeline_ok", sid=state.get("session_id"))
        except Exception as exc:
            logger.error("delivery_pipeline_failed", error=str(exc), sid=state.get("session_id"))

        # 3. Emergency SMS
        if emergency_sms_fn:
            await emergency_sms_fn(state)

        state["duration_ms"] = _elapsed(start)
        return state

    return node_finalize_and_deliver


def build_post_chat_graph(state_schema: Any, nodes_dict: dict) -> Callable:
    def builder():
        g = StateGraph(state_schema)
        g.add_node("score_lead", nodes_dict["score_lead"])
        g.add_node("deliver",    nodes_dict["deliver"])
        g.set_entry_point("score_lead")
        g.add_conditional_edges(
            "score_lead", _route_post_score,
            {"go": "deliver", "skip": END}
        )
        g.add_edge("deliver", END)
        return g.compile()
    return builder