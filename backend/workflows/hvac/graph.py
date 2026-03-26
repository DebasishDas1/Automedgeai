# workflows/hvac/graph.py
from __future__ import annotations

from workflows.shared import build_chat_graph, build_post_chat_graph
from workflows.hvac.nodes import (
    node_check_completion,
    node_chat_reply,
    node_enrich_lead,
    node_finalize_and_deliver,
    node_score_lead,
    node_validate_input,
)
from workflows.hvac.state import HvacState

def build_hvac_chat_graph():
    return build_chat_graph(HvacState, {
        "validate": node_validate_input,
        "enrich": node_enrich_lead,
        "check_done": node_check_completion,
        "reply": node_chat_reply,
    }, always_reply=False)()

def build_hvac_post_chat_graph():
    return build_post_chat_graph(HvacState, {
        "score_lead": node_score_lead,
        "deliver": node_finalize_and_deliver,
    })()
