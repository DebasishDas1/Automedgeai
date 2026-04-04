# api/v1/chat/router.py
from __future__ import annotations
from fastapi import APIRouter, Depends, BackgroundTasks, Request
from fastapi.responses import StreamingResponse

from api.deps import get_db
from api.v1.chat.base import (
    MessageRequest,
    MessageResponse,
    StartRequest,
    StartResponse,
    handle_message,
    handle_message_stream,
    handle_start,
)

router = APIRouter()

@router.post(
    "/start",
    response_model=StartResponse,
    status_code=201,
    summary="Start a new chat session",
    tags=["Chat • Operations"]
)
async def start(body: StartRequest, db=Depends(get_db)):
    """
    Consolidated entry point for starting ANY business vertical session.
    The vertical must be specified in the request body.
    """
    return await handle_start(body.vertical, body, db)


@router.post(
    "/message",
    response_model=MessageResponse,
    summary="Send a message",
    tags=["Chat • Operations"]
)
async def message(
    request: Request,
    background_tasks: BackgroundTasks,
    body: MessageRequest,
    db=Depends(get_db),
):
    """Universal message handler — routing is session-id based."""
    return await handle_message(body, db, background_tasks, request)


@router.post(
    "/message/stream",
    response_class=StreamingResponse,
    summary="Stream AI reply via SSE",
    tags=["Chat • Operations"]
)
async def message_stream(
    request: Request,
    background_tasks: BackgroundTasks,
    body: MessageRequest,
    db=Depends(get_db),
):
    """SSE streaming handler for all verticals."""
    return await handle_message_stream(body, db, background_tasks, request)
