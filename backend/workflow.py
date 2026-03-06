import asyncio
import json
from typing import Dict
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

router = APIRouter()

async def demo_workflow_generator(vertical: str):
    steps = [
        {"step": 1, "label": "Lead Captured", "status": "active", "ts": "0s"},
        {"step": 2, "label": "AI Qualification", "status": "active", "ts": "1.8s"},
        {"step": 3, "label": "SMS Sent", "status": "active", "ts": "3.6s"},
        {"step": 4, "label": "Call Booked", "status": "active", "ts": "5.4s"},
    ]
    
    for step in steps:
        await asyncio.sleep(1.8)
        yield f"data: {json.dumps(step)}\n\n"
    
    yield "data: [DONE]\n\n"

@router.get("/api/workflow/stream")
async def stream_workflow(vertical: str = Query(...)):
    return StreamingResponse(
        demo_workflow_generator(vertical),
        media_type="text/event-stream"
    )
