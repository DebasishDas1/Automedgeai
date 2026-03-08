# workflows/roofing/graph.py
# Roofing post-chat routing is driven by the insurance signal.
#
# TWO GRAPHS:
#   roofing_chat_graph      — live chat turns, <500ms, called per message
#   roofing_post_chat_graph — background, runs once on completion
#
# POST-CHAT ROUTING:
#   storm + insurance path -> insurance_sms -> score_lead -> summary -> email -> sheets
#   all other paths        -> score_lead -> summary -> email (if not cold) -> sheets
#
# INSURANCE SMS RATIONALE:
#   Storm+insurance leads get a pre-inspection SMS reminding them to have
#   their policy number ready. No other vertical does this.
#   Purpose: improves show rate. Homeowner feels more prepared and committed.
#   Roofing inspections are ~1hr, high no-show risk without engagement.
#
# EMAIL ROUTING:
#   cold + planning urgency -> skip email (browsing, no commitment)
#   everything else         -> send email
#   storm+insurance email   -> includes claim guidance section (set in nodes.py)
from langgraph.graph import StateGraph, END

from workflows.roofing.nodes import (
    node_check_complete,
    node_chat_reply,
    node_extract_fields,
    node_extract_final,
    node_score_urgency,
    node_insurance_sms,
    node_score_lead,
    node_generate_summary,
    node_send_email,
    node_save_sheets,
)


# ══════════════════════════════════════════════════════════════════════════════
# GRAPH 1 — chat_graph
# ══════════════════════════════════════════════════════════════════════════════

def build_roofing_chat_graph() -> StateGraph:
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
# ══════════════════════════════════════════════════════════════════════════════

def build_roofing_post_chat_graph() -> StateGraph:
    g = StateGraph(dict)

    g.add_node("extract_final",    node_extract_final)
    g.add_node("score_urgency",    node_score_urgency)
    g.add_node("insurance_sms",    node_insurance_sms)
    g.add_node("score_lead",       node_score_lead)
    g.add_node("generate_summary", node_generate_summary)
    g.add_node("send_email",       node_send_email)
    g.add_node("save_sheets",      node_save_sheets)

    g.set_entry_point("extract_final")
    g.add_edge("extract_final", "score_urgency")

    # Storm+insurance leads get pre-inspection SMS
    g.add_conditional_edges(
        "score_urgency",
        route_insurance_sms,
        {
            "insurance_sms": "insurance_sms",
            "skip_sms":      "score_lead",
        },
    )

    g.add_edge("insurance_sms",    "score_lead")
    g.add_edge("score_lead",       "generate_summary")

    # Cold + planning = skip email
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


def route_insurance_sms(state: dict) -> str:
    """
    Send pre-inspection insurance reminder SMS only for storm+insurance leads.
    All other leads skip directly to scoring.
    """
    is_storm    = state.get("damage_type") == "storm"
    has_ins     = state.get("has_insurance") is True
    has_phone   = bool(state.get("phone"))
    appt_booked = state.get("appt_booked")

    # SMS only useful if they have a phone and an appointment to remind about
    if is_storm and has_ins and has_phone and appt_booked:
        return "insurance_sms"
    return "skip_sms"


def route_email(state: dict) -> str:
    """
    Skip email for cold leads with planning urgency only (just browsing).
    All storm, leak, and inspection_needed leads get email regardless of score.
    """
    urgency = state.get("urgency", "inspection_needed")
    score   = state.get("score", "warm")
    email   = state.get("email")

    if not email:
        return "no_email"

    # Only skip email for cold leads who were just planning/browsing
    if score == "cold" and urgency == "planning":
        return "no_email"

    return "email"


# ══════════════════════════════════════════════════════════════════════════════
# Compiled instances — imported by services/workflow_service.py
# ══════════════════════════════════════════════════════════════════════════════

roofing_chat_graph      = build_roofing_chat_graph()
roofing_post_chat_graph = build_roofing_post_chat_graph()