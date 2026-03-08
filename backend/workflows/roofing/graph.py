from langgraph.graph import StateGraph, END
from workflows.base import LeadState, capture_lead, send_sms, request_review
from workflows.roofing.nodes import score_urgency, dispatch_tech, book_appointment

def build_roofing_graph() -> StateGraph:
    graph = StateGraph(LeadState)
    graph.add_node("capture",   capture_lead)
    graph.add_node("score",     score_urgency)
    graph.add_node("sms",       send_sms)
    graph.add_node("dispatch",  dispatch_tech)
    graph.add_node("book",      book_appointment)
    graph.add_node("review",    request_review)

    graph.set_entry_point("capture")
    graph.add_edge("capture",  "score")
    graph.add_edge("score",    "sms")
    graph.add_edge("sms",      "dispatch")
    graph.add_edge("dispatch", "book")
    graph.add_edge("book",     "review")
    graph.add_edge("review",   END)
    return graph.compile()

roofing_graph = build_roofing_graph()
