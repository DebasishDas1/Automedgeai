# workflows/plumbing/graph.py
from __future__ import annotations

from langgraph.graph import StateGraph, END

from workflows.plumbing.nodes import (
    node_validate_input,
    node_enrich_lead,
    node_check_completion,
    node_chat_reply,
    node_score_lead,
    node_finalize_and_deliver,
)
from workflows.plumbing.state import PlumbingState


def _route_completion(state: dict) -> str:
    return "complete" if state.get("is_complete") else "continue"


def _route_post_score(state: dict) -> str:
    if state.get("is_spam") or state.get("next_step") == "drop":
        return "skip"
    return "go"


def build_plumbing_chat_graph():
    g = StateGraph(PlumbingState)

    g.add_node("validate",   node_validate_input)
    g.add_node("enrich",     node_enrich_lead)
    g.add_node("check_done", node_check_completion)
    g.add_node("reply",      node_chat_reply)

    g.set_entry_point("validate")
    g.add_edge("validate",   "enrich")
    g.add_edge("enrich",     "check_done")
    # Both paths go through reply — user always gets a response
    g.add_conditional_edges(
        "check_done",
        _route_completion,
        {"complete": "reply", "continue": "reply"},
    )
    g.add_edge("reply", END)

    return g.compile()


def build_plumbing_post_chat_graph():
    g = StateGraph(PlumbingState)

    g.add_node("score_lead", node_score_lead)
    g.add_node("deliver",    node_finalize_and_deliver)

    g.set_entry_point("score_lead")
    g.add_conditional_edges("score_lead", _route_post_score,
                            {"go": "deliver", "skip": END})
    g.add_edge("deliver", END)

    return g.compile()