# workflows/shared.py
from __future__ import annotations

import json
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

def build_validate_input_node(_MAX_TURNS: int = 10) -> Callable:
    """Creates a generic validation node."""
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
    """Creates a generic completion checker based on required fields."""
    async def node_check_completion(state: dict) -> dict:
        if state.get("is_complete"):
            return state
        if all(not field_missing(state, f) for f in required_fields):
            state["is_complete"] = True
        return state
    return node_check_completion

def build_chat_reply_node(system_prompt_template: str, fields_to_collect: tuple[str, ...]) -> Callable:
    """Creates a generic chat reply node that avoids state leaks."""
    async def node_chat_reply(state: dict) -> dict:
        # Build list of already collected fields (cleaned)
        collected = {
            k: state.get(k)
            for k in fields_to_collect
            if state.get(k) is not None
        }

        # Some prompts expect `slots` to be passed, some don't, but we pass them via **kwargs later if needed,
        # or just format JSON into the `collected` placeholder.
        # This assumes the prompt has a `{collected}` placeholder.
        try:
            system_prompt = system_prompt_template.format(
                collected=json.dumps(collected, ensure_ascii=False)
            )
        except KeyError:
            # Fallback if the prompt requires other things like slots
            # This is specifically for Pest/HVAC/Roofing that use {collected} and {slot_1} etc.
            kwargs = {"collected": json.dumps(collected, ensure_ascii=False)}
            from workflows.base import get_appt_slots
            slots = state.get("appt_slots") or get_appt_slots()
            state["appt_slots"] = slots
            for i, slot in enumerate(slots):
                kwargs[f"slot_{i+1}"] = slot
            system_prompt = system_prompt_template.format(**kwargs)

        # Last user message (safe)
        last_user = next(
            (m["content"] for m in reversed(state.get("messages", [])) if m.get("role") == "user"),
            ""
        )

        reply = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=last_user)
        ])

        assistant_text = reply.content.strip()
        if assistant_text.startswith("```"):
            assistant_text = assistant_text.split("```")[-1].strip()

        new_messages = list(state.get("messages", []))
        new_messages.append({"role": "assistant", "content": assistant_text})

        return {
            **state,
            "messages": new_messages,
            "turn_count": state.get("turn_count", 0) + 1,
            "last_node": "reply",
        }
    return node_chat_reply

def _route_completion(state: dict) -> str:
    return "complete" if state.get("is_complete") else "continue"

def _route_post_score(state: dict) -> str:
    if state.get("is_spam") or state.get("next_step") == "drop":
        return "skip"
    return "go"

def build_chat_graph(state_schema: Any, nodes_dict: dict, always_reply: bool = True) -> Callable:
    """
    Creates a standardized Chat Graph compilation.
    nodes_dict must contain: 'validate', 'enrich', 'check_done', 'reply'
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
        
        edges = {"complete": "reply", "continue": "reply"} if always_reply else {"complete": END, "continue": "reply"}
        g.add_conditional_edges("check_done", _route_completion, edges)
        
        g.add_edge("reply", END)
        return g.compile()
    
    return builder

def build_post_chat_graph(state_schema: Any, nodes_dict: dict) -> Callable:
    """
    Creates a standardized Post Chat Graph compilation.
    nodes_dict must contain: 'score_lead', 'deliver'
    """
    def builder():
        g = StateGraph(state_schema)

        g.add_node("score_lead", nodes_dict["score_lead"])
        g.add_node("deliver",    nodes_dict["deliver"])

        g.set_entry_point("score_lead")
        g.add_conditional_edges("score_lead", _route_post_score, {"go": "deliver", "skip": END})
        g.add_edge("deliver", END)

        return g.compile()
    
    return builder
