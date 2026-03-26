# workflows/pest_control/graph.py
from __future__ import annotations

from workflows.shared import build_chat_graph, build_post_chat_graph
from workflows.pest_control.nodes import (
    node_check_completion,
    node_chat_reply,
    node_enrich_lead,
    node_finalize_and_deliver,
    node_score_lead,
    node_validate_input,
)
from workflows.pest_control.state import PestState

def build_pest_chat_graph():
    return build_chat_graph(PestState, {
        "validate": node_validate_input,
        "enrich": node_enrich_lead,
        "check_done": node_check_completion,
        "reply": node_chat_reply,
    }, always_reply=True)()

def build_pest_post_chat_graph():
    return build_post_chat_graph(PestState, {
        "score_lead": node_score_lead,
        "deliver": node_finalize_and_deliver,
    })()
