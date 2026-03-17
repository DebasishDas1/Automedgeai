# api/v1/chat/base.py
# Shared request/response models and handler functions.

import structlog
import json
from typing import Literal, AsyncGenerator
from fastapi import BackgroundTasks, HTTPException, status
from fastapi.responses import ORJSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from services import workflow_service
from workflows.registry import registry

logger = structlog.get_logger(__name__)
Vertical = Literal["hvac", "pest_control", "plumbing", "roofing"]

class StartRequest(BaseModel):
    source: str | None = None

class StartResponse(BaseModel):
    session_id: str
    vertical:   Vertical
    turn:       int = 0

class MessageRequest(BaseModel):
    session_id: str
    message: str = Field(..., min_length=1, max_length=1000)

class MessageResponse(BaseModel):
    session_id:       str
    message:          str   # AI reply
    turn:             int
    is_complete:      bool
    appt_booked:      bool
    fields_collected: dict 

async def handle_start(vertical: Vertical, body: StartRequest, db) -> dict:
    try:
        return await workflow_service.start_session(db=db, vertical=vertical)
    except Exception as e:
        logger.error("start_chat_failed", error=str(e))
        raise HTTPException(status_code=500, detail="start_failed")

async def handle_message(body: MessageRequest, db) -> dict:
    try:
        return await workflow_service.send_message(db=db, session_id=body.session_id, user_msg=body.message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("message_failed", session=body.session_id, error=str(e))
        raise HTTPException(status_code=500, detail="processing_error")

async def handle_message_stream(body: MessageRequest, db) -> StreamingResponse:
    from core.database import ChatSession, select
    res = await db.execute(select(ChatSession).where(ChatSession.session_id == body.session_id))
    row = res.scalar_one_or_none()
    if not row or row.is_complete: raise HTTPException(status_code=400, detail="invalid_session")

    async def stream():
        graph = registry.get_chat_graph(row.vertical)
        state = dict(row.state)
        state.setdefault("messages", []).append({"role": "user", "content": body.message})
        
        async for event in graph.astream_events(state, version="v1"):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"].content
                if chunk: yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            elif event["event"] == "on_chain_end" and event["name"] == "LangGraph":
                await workflow_service._save_session(db, row, event["data"]["output"])
                yield "data: [DONE]\n\n"
    return StreamingResponse(stream(), media_type="text/event-stream")