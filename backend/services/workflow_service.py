from workflows.hvac.graph      import hvac_graph
from workflows.roofing.graph   import roofing_graph
from workflows.plumbing.graph  import plumbing_graph
from workflows.pest_control.graph import pest_graph

GRAPHS = {
    "hvac":         hvac_graph,
    "roofing":      roofing_graph,
    "plumbing":     plumbing_graph,
    "pest_control": pest_graph,
}

async def run_workflow(vertical: str, lead: dict):
    graph = GRAPHS.get(vertical)
    if not graph:
        raise ValueError(f"Unknown vertical: {vertical}")
    return graph.astream(lead)   # async stream → SSE to frontend