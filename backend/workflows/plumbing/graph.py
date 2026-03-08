# workflows/plumbing/graph.py
# Plumbing has the most complex routing of all 4 verticals.
# Emergency path: SMS dispatch immediately, skip slot selection entirely.
# Routine path: standard chat -> appointment -> email -> sheets.
#
# TWO GRAPHS:
#   plumbing_chat_graph      — live chat turns, <500ms, called per message
#   plumbing_post_chat_graph — background, runs once on completion
#
# EMERGENCY ROUTING in post_chat_graph:
#   emergency -> emergency_sms -> score_lead -> summary -> email -> sheets
#   urgent    -> score_lead -> summary -> email -> sheets
#   routine   -> score_lead -> summary -> email (if not cold) -> sheets
from langgraph.graph import StateGraph, END

from workflows.plumbing.nodes import (
    node_check_complete,
    node_chat_reply,
    node_extract_fields,
    node_extract_final,
    node_score_urgency,
    node_emergency_sms,
    node_score_lead,
    node_generate_summary,
    node_send_email,
    node_save_sheets,
)


# ══════════════════════════════════════════════════════════════════════════════
# GRAPH 1 — chat_graph
# Runs on every user message. Must be fast (<500ms).
# ══════════════════════════════════════════════════════════════════════════════

def build_plumbing_chat_graph() -> StateGraph:
    g = StateGraph(dict)

    g.add_node("check_complete", node_check_complete)
    g.add_node("chat_reply",     node_chat_reply)
    g.add_node("extract_fields", node_extract_fields)

    g.set_entry_point("check_complete")

    g.add_conditional_edges(
        "check_complete",
        route_chat,
        {
            "complete": END,
            "continue": "chat_reply",
        },
    )
    g.add_edge("chat_reply",     "extract_fields")
    g.add_edge("extract_fields", END)

    return g.compile()


def route_chat(state: dict) -> str:
    return "complete" if state.get("is_complete") else "continue"


# ══════════════════════════════════════════════════════════════════════════════
# GRAPH 2 — post_chat_graph
# Runs once in background when conversation ends.
# Triggered by FastAPI BackgroundTasks after is_complete=True.
#
# Three paths based on urgency:
#
#   EMERGENCY path:
#     extract_final -> score_urgency -> emergency_sms -> score_lead
#       -> generate_summary -> send_email -> save_sheets
#     Rationale: SMS goes out immediately before anything else.
#     Water damage compounds by the minute — dispatch cannot wait for
#     summary generation or sheet saving.
#
#   URGENT path (significant leak, no hot water, toilet overflow):
#     extract_final -> score_urgency -> score_lead
#       -> generate_summary -> send_email -> save_sheets
#     No SMS — urgent but not active flooding. Email is sufficient.
#
#   ROUTINE path (slow drain, dripping faucet, running toilet):
#     extract_final -> score_urgency -> score_lead
#       -> generate_summary -> send_email (skip if cold) -> save_sheets
#     Cold routine leads skip email — saves Resend quota.
# ══════════════════════════════════════════════════════════════════════════════

def build_plumbing_post_chat_graph() -> StateGraph:
    g = StateGraph(dict)

    g.add_node("extract_final",    node_extract_final)
    g.add_node("score_urgency",    node_score_urgency)
    g.add_node("emergency_sms",    node_emergency_sms)
    g.add_node("score_lead",       node_score_lead)
    g.add_node("generate_summary", node_generate_summary)
    g.add_node("send_email",       node_send_email)
    g.add_node("save_sheets",      node_save_sheets)

    g.set_entry_point("extract_final")
    g.add_edge("extract_final", "score_urgency")

    # Route based on urgency level
    g.add_conditional_edges(
        "score_urgency",
        route_by_urgency,
        {
            "emergency": "emergency_sms",  # SMS first, immediately
            "non_emergency": "score_lead", # skip SMS for urgent/routine
        },
    )

    # Emergency SMS rejoins at score_lead
    g.add_edge("emergency_sms",    "score_lead")
    g.add_edge("score_lead",       "generate_summary")

    # Route based on score — skip email for cold routine leads
    g.add_conditional_edges(
        "generate_summary",
        route_email,
        {
            "email":    "send_email",
            "no_email": "save_sheets",
        },
    )
    g.add_edge("send_email", "save_sheets")
    g.add_edge("save_sheets", END)

    return g.compile()


def route_by_urgency(state: dict) -> str:
    """
    Sends emergency SMS before anything else.
    Urgent and routine skip SMS — email confirmation is sufficient.
    """
    urgency = state.get("urgency", "routine")
    return "emergency" if urgency == "emergency" else "non_emergency"


def route_email(state: dict) -> str:
    """
    Skip email for cold leads with no email OR cold + routine (low conversion).
    Always send for emergency and urgent regardless of score.
    """
    urgency = state.get("urgency", "routine")
    score   = state.get("score", "warm")
    email   = state.get("email")

    # Emergency/urgent always get email if they have one
    if urgency in ("emergency", "urgent"):
        return "email" if email else "no_email"

    # Routine cold leads — skip email, not worth Resend quota
    if not email or score == "cold":
        return "no_email"

    return "email"


# ══════════════════════════════════════════════════════════════════════════════
# Compiled instances — imported by services/workflow_service.py
# ══════════════════════════════════════════════════════════════════════════════

plumbing_chat_graph      = build_plumbing_chat_graph()
plumbing_post_chat_graph = build_plumbing_post_chat_graph()