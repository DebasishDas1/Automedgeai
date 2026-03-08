from langgraph.graph import StateGraph, END

from workflows.pest_control.nodes import (
    node_check_complete,
    node_chat_reply,
    node_extract_fields,
    node_extract_final,
    node_score_urgency,
    node_score_lead,
    node_generate_summary,
    node_send_email,
    node_save_sheets,
)


# ══════════════════════════════════════════════════════════════════════════════
# GRAPH 1 — chat_graph
# Runs on every user message turn. Must be fast (<500ms).
# Triggered by: POST /chat/message
# ══════════════════════════════════════════════════════════════════════════════

def build_pest_chat_graph() -> StateGraph:
    g = StateGraph(dict)

    g.add_node("check_complete", node_check_complete)
    g.add_node("chat_reply",     node_chat_reply)
    g.add_node("extract_fields", node_extract_fields)

    g.set_entry_point("check_complete")

    # If complete -> END (triggers post_chat_graph as background task)
    # If not complete -> reply -> extract -> END
    g.add_conditional_edges(
        "check_complete",
        route_chat,
        {
            "complete":    END,
            "continue":    "chat_reply",
        },
    )
    g.add_edge("chat_reply",     "extract_fields")
    g.add_edge("extract_fields", END)

    return g.compile()


def route_chat(state: dict) -> str:
    return "complete" if state.get("is_complete") else "continue"


# ══════════════════════════════════════════════════════════════════════════════
# GRAPH 2 — post_chat_graph
# Runs ONCE when conversation ends. Runs in background.
# Triggered by: FastAPI BackgroundTasks after is_complete=True
#
# Routing logic:
#   high urgency   -> score_urgency -> score_lead -> summary -> email -> sheets
#   medium urgency -> score_urgency -> score_lead -> summary -> email -> sheets
#   low urgency    -> score_urgency -> score_lead -> summary -> sheets (skip email)
#
# LOW urgency (spiders, unknown) skips email — not worth sending for cold leads.
# Saves Resend quota and avoids spammy emails to browsers/curious visitors.
# ══════════════════════════════════════════════════════════════════════════════

def build_pest_post_chat_graph() -> StateGraph:
    g = StateGraph(dict)

    g.add_node("extract_final",   node_extract_final)
    g.add_node("score_urgency",   node_score_urgency)
    g.add_node("score_lead",      node_score_lead)
    g.add_node("generate_summary",node_generate_summary)
    g.add_node("send_email",      node_send_email)
    g.add_node("save_sheets",     node_save_sheets)

    g.set_entry_point("extract_final")
    g.add_edge("extract_final",    "score_urgency")
    g.add_edge("score_urgency",    "score_lead")
    g.add_edge("score_lead",       "generate_summary")

    # Conditional: send email only if urgency is not low
    # Low urgency = cold lead = spiders/unknown = skip email
    g.add_conditional_edges(
        "generate_summary",
        route_post_chat,
        {
            "email":    "send_email",
            "no_email": "save_sheets",
        },
    )
    g.add_edge("send_email", "save_sheets")
    g.add_edge("save_sheets", END)

    return g.compile()


def route_post_chat(state: dict) -> str:
    """
    Skip email for cold leads with no email or low urgency pest.
    Saves Resend quota. Low urgency = spiders/unknown + no appointment booked.
    """
    score   = state.get("score", "warm")
    urgency = state.get("urgency", "medium")
    email   = state.get("email")

    # Always send if email collected and not cold score
    if not email:
        return "no_email"

    if score == "cold" and urgency == "low":
        return "no_email"

    return "email"


# ══════════════════════════════════════════════════════════════════════════════
# Compiled graph instances — imported by services/workflow_service.py
# ══════════════════════════════════════════════════════════════════════════════

pest_chat_graph      = build_pest_chat_graph()
pest_post_chat_graph = build_pest_post_chat_graph()