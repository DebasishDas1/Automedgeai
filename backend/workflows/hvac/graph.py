from langgraph.graph import StateGraph, END
from models.workflow import HVACChatState
from workflows.hvac.nodes import (
    node_check_complete, 
    node_chat_reply, 
    node_extract_fields, 
    node_extract_final, 
    node_score_lead, 
    node_generate_summary, 
    node_send_email, 
    node_save_sheets
)


def route_complete(state: HVACChatState) -> str:
    if state.get("is_complete"):
        return END
    return "chat_reply"


def build_chat_graph():
    graph = StateGraph(HVACChatState)

    graph.add_node("check_complete", node_check_complete)
    graph.add_node("chat_reply", node_chat_reply)
    graph.add_node("extract_fields", node_extract_fields)

    graph.set_entry_point("check_complete")
    graph.add_conditional_edges("check_complete", route_complete)
    graph.add_edge("chat_reply", "extract_fields")
    graph.add_edge("extract_fields", END)

    return graph.compile()



def build_post_chat_graph():
    graph = StateGraph(HVACChatState)
    
    graph.add_node("extract_final", node_extract_final)
    graph.add_node("score_lead", node_score_lead)
    graph.add_node("generate_summary", node_generate_summary)
    graph.add_node("send_email", node_send_email)
    graph.add_node("save_sheets", node_save_sheets)
    
    graph.set_entry_point("extract_final")
    graph.add_edge("extract_final", "score_lead")
    graph.add_edge("score_lead", "generate_summary")
    graph.add_edge("generate_summary", "send_email")
    graph.add_edge("send_email", "save_sheets")
    graph.add_edge("save_sheets", END)
    
    return graph.compile()



hvac_chat_graph = build_chat_graph()
post_hvac_chat_graph = build_post_chat_graph()