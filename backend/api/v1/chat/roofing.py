# api/v1/chat/roofing.py
from fastapi import APIRouter, Depends
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

router = APIRouter(prefix="/roofing")

_VERTICAL = "roofing"


@router.post("/start", response_model=StartResponse, status_code=201,
             summary="Start a roofing chat session")
async def start(body: StartRequest, db=Depends(get_db)):
    """Create a new roofing lead capture session."""
    return await handle_start(_VERTICAL, body, db)


@router.post("/message", response_model=MessageResponse,
             summary="Send a message in a roofing session")
async def message(body: MessageRequest, db=Depends(get_db)):
    """Send a user message and receive the AI reply."""
    return await handle_message(body, db)


@router.post("/message/stream", response_class=StreamingResponse,
             summary="Stream a roofing AI reply via SSE")
async def message_stream(body: MessageRequest, db=Depends(get_db)):
    """SSE endpoint. data: {chunk} per token, data: [DONE] on finish."""
    return await handle_message_stream(body, db)