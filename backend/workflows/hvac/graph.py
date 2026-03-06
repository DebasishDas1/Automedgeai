from langgraph.graph import StateGraph, END
from workflows.base import LeadState, capture_lead, send_sms
from workflows.hvac.nodes import score_urgency, dispatch_tech, book_appointment

def build_hvac_graph() -> StateGraph:
    graph = StateGraph(LeadState)

    # Nodes — shared + HVAC-specific
    graph.add_node("capture",   capture_lead)
    graph.add_node("score",     score_urgency)    # HVAC: emergency vs routine
    graph.add_node("sms",       send_sms)
    graph.add_node("dispatch",  dispatch_tech)
    graph.add_node("book",      book_appointment)
    graph.add_node("review",    request_review)

    # Edges
    graph.set_entry_point("capture")
    graph.add_edge("capture",  "score")
    graph.add_edge("score",    "sms")
    graph.add_edge("sms",      "dispatch")
    graph.add_edge("dispatch", "book")
    graph.add_edge("book",     "review")
    graph.add_edge("review",   END)

    return graph.compile()

hvac_graph = build_hvac_graph()