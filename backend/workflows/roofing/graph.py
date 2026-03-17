from langgraph.graph import StateGraph, END
from workflows.roofing.nodes import (
    node_check_complete,
    node_chat_reply,
    node_extract_fields,
    node_save_and_email
)

def build_roofing_chat_graph() -> StateGraph:
    g = StateGraph(dict)
    g.add_node("check_complete", node_check_complete)
    g.add_node("chat_reply",     node_chat_reply)
    g.add_node("extract_fields", node_extract_fields)

    g.set_entry_point("check_complete")
    g.add_conditional_edges(
        "check_complete",
        lambda state: "complete" if state.get("is_complete") else "continue",
        {"complete": END, "continue": "chat_reply"},
    )
    g.add_edge("chat_reply",     "extract_fields")
    g.add_edge("extract_fields", END)
    return g.compile()

def build_roofing_post_chat_graph() -> StateGraph:
    g = StateGraph(dict)
    g.add_node("save_and_email", node_save_and_email)
    g.set_entry_point("save_and_email")
    g.add_edge("save_and_email", END)
    return g.compile()