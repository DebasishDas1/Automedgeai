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


# ── Node builders ─────────────────────────────────────────────────────────────

def build_validate_input_node(_MAX_TURNS: int = 10) -> Callable:
    async def node_validate_input(state: dict) -> dict:
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
    return node_validate_input


def build_check_completion_node(required_fields: tuple[str, ...]) -> Callable:
    """
    Session completes when all required fields are collected AND either:
      - the user doesn't want an appointment, OR
      - an appointment has been confirmed.

    This keeps the session open after data collection so the bot can offer
    and confirm a slot before triggering the post-chat pipeline.
    """
    async def node_check_completion(state: dict) -> dict:
        if state.get("is_complete"):
            return state

        # Required fields not yet collected — stay open
        if not all(not field_missing(state, f) for f in required_fields):
            return state

        # All required fields collected. Check appointment state.
        wants_appt = state.get("wants_appointment")
        appt_confirmed = state.get("appt_confirmed")
        appt_booked = state.get("appt_booked")

        # If user explicitly doesn't want an appointment, complete immediately
        if wants_appt is False:
            state["is_complete"] = True
            return state

        # If appointment confirmed or booked, complete
        if appt_confirmed or appt_booked:
            state["is_complete"] = True
            return state

        # wants_appointment=True but not yet confirmed — stay open for booking
        if wants_appt is True:
            return state

        # wants_appointment=None (not asked yet): complete after enough turns
        # Give the bot 2 turns to offer slots before forcing completion
        turn_count = int(state.get("turn_count", 0))
        if turn_count >= 3:
            state["is_complete"] = True

        return state
    return node_check_completion


def build_chat_reply_node(
    system_prompt_template: str,
    fields_to_collect: tuple[str, ...],
) -> Callable:
    """
    Chat reply node. Handles:
    - Slot formatting (slot_1, slot_2, slot_3 placeholders)
    - Code fence stripping from model output
    - Appointment confirmation detection from assistant reply
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

        reply = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=last_user),
        ])

        # Strip code fences (model sometimes wraps output)
        assistant_text = reply.content.strip()
        assistant_text = re.sub(r"^```[a-z]*\n?", "", assistant_text).strip()
        assistant_text = re.sub(r"```$", "", assistant_text).strip()

        new_messages = list(state.get("messages", []))
        new_messages.append({"role": "assistant", "content": assistant_text})

        updated = {
            **state,
            "messages":    new_messages,
            "turn_count":  state.get("turn_count", 0) + 1,
            "last_node":   "reply",
        }

        # Detect appointment confirmation from the assistant's own reply text.
        # If the bot confirms a specific slot, mark it as booked in state.
        if not updated.get("appt_booked") and not updated.get("appt_confirmed"):
            appt_slots = updated.get("appt_slots") or []
            reply_lower = assistant_text.lower()
            for slot in appt_slots:
                if slot.lower() in reply_lower or "you're all set" in reply_lower:
                    updated["appt_booked"]    = True
                    updated["appt_confirmed"] = slot
                    logger.info("appointment_confirmed_from_reply",
                                session_id=updated.get("session_id"), slot=slot)
                    break

        return updated
    return node_chat_reply


# ── Routing ───────────────────────────────────────────────────────────────────

def _route_completion(state: dict) -> str:
    return "complete" if state.get("is_complete") else "continue"


def _route_post_score(state: dict) -> str:
    if state.get("is_spam") or state.get("next_step") == "drop":
        return "skip"
    return "go"


# ── Graph builders ────────────────────────────────────────────────────────────

def build_chat_graph(
    state_schema: Any,
    nodes_dict: dict,
    always_reply: bool = True,
) -> Callable:
    """
    Standardized chat graph: validate → enrich → check_done → reply → END
    nodes_dict keys: 'validate', 'enrich', 'check_done', 'reply'
    """
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


def build_post_chat_graph(state_schema: Any, nodes_dict: dict) -> Callable:
    """
    Standardized post-chat graph: score_lead → deliver → END
    nodes_dict keys: 'score_lead', 'deliver'
    """
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