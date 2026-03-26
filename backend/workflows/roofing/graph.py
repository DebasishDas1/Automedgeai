# workflows/roofing/graph.py
from __future__ import annotations

from workflows.shared import build_chat_graph, build_post_chat_graph
from workflows.roofing.nodes import (
    node_check_completion,
    node_chat_reply,
    node_enrich_lead,
    node_finalize_and_deliver,
    node_score_lead,
    node_validate_input,
)
from workflows.roofing.state import RoofingState

def build_roofing_chat_graph():
    return build_chat_graph(RoofingState, {
        "validate": node_validate_input,
        "enrich": node_enrich_lead,
        "check_done": node_check_completion,
        "reply": node_chat_reply,
    }, always_reply=True)()

def build_roofing_post_chat_graph():
    return build_post_chat_graph(RoofingState, {
        "score_lead": node_score_lead,
        "deliver": node_finalize_and_deliver,
    })()
