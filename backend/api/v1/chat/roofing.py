# api/v1/chat/roofing.py
from fastapi import APIRouter, Depends
from api.deps import get_db
from api.v1.chat.base import (
    StartRequest, MessageRequest, handle_start, handle_message
)

router = APIRouter()
_VERTICAL = "roofing"

@router.post("/start", status_code=201)
async def start(body: StartRequest, db=Depends(get_db)):
    return await handle_start(_VERTICAL, body, db)

@router.post("/message")
async def message(body: MessageRequest, db=Depends(get_db)):
    return await handle_message(body, db)