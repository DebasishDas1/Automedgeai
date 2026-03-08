from workflows.hvac.graph      import hvac_graph
from workflows.roofing.graph   import roofing_graph
from workflows.plumbing.graph  import plumbing_graph
from workflows.pest_control.graph import pest_graph
import json
import asyncio
from typing import AsyncGenerator

GRAPHS = {
    "hvac":         hvac_graph,
    "roofing":      roofing_graph,
    "plumbing":     plumbing_graph,
    "pest_control": pest_graph,
}

class WorkflowService:
    @staticmethod
    async def stream_workflow(vertical: str, state: dict) -> AsyncGenerator[str, None]:
        graph = GRAPHS.get(vertical)
        if not graph:
            yield f"data: {json.dumps({'type': 'error', 'message': f'Unknown vertical: {vertical}'})}\n\n"
            return

        try:
            # We use astream to get events as they happen
            async for event in graph.astream(state):
                # LangGraph events look like { 'node_name': { 'state_updates' } }
                # We want to yield the 'events' list updates
                for node_name, updates in event.items():
                    if "events" in updates:
                        # Yield only the latest event
                        latest_event = updates["events"][-1]
                        yield f"data: {json.dumps({'type': 'event', 'data': latest_event})}\n\n"
            
            yield f"data: {json.dumps({'type': 'complete', 'message': 'Workflow finished'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

workflow_service = WorkflowService()