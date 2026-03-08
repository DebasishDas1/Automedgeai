import uuid
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db, ChatSession
from models.workflow import HVACChatState
from pydantic import BaseModel
from services.workflow_service import run_chat_turn, run_post_chat

router = APIRouter()
logger = logging.getLogger(__name__)

class ChatStartRequest(BaseModel):
    vertical: str = "hvac"

class ChatMessageRequest(BaseModel):
    session_id: str
    message: str

@router.post("/start")
async def start_chat(req: ChatStartRequest, db: AsyncSession = Depends(get_db)):
    if req.vertical != "hvac":
        raise HTTPException(status_code=400, detail="Only hvac vertical supported for now")
        
    session_id = str(uuid.uuid4())
    initial_state: HVACChatState = {
        "session_id": session_id,
        "user_id": None,
        "started_at": datetime.now().isoformat(),
        "messages": [],
        "turn_count": 0,
        "is_complete": False,
        "name": None, "email": None, "phone": None, "location": None, "issue": None,
        "system_age": None, "urgency": None, "is_homeowner": None, "budget_signal": None, "timeline": None,
        "appt_offered": False, "appt_slots": [], "appt_confirmed": None, "appt_booked": False,
        "summary": None, "score": None, "score_reason": None, "email_sent": False,
        "sheet_row": None, "sheet_tab": None
    }
    
    opening_message = "Hi! I'm Alex, an HVAC technician. What's going on with your system today?"
    initial_state["messages"].append({
        "role": "assistant",
        "content": opening_message,
        "ts": datetime.now().isoformat()
    })
    
    new_session = ChatSession(
        session_id=session_id,
        vertical=req.vertical,
        state=initial_state
    )
    db.add(new_session)
    await db.commit()
    
    return {
        "session_id": session_id,
        "message": opening_message,
        "turn": 0
    }

@router.post("/message")
async def chat_message(req: ChatMessageRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    if len(req.message) > 1000:
        raise HTTPException(status_code=400, detail="Message too long")
        
    try:
        reply_data = await run_chat_turn(req.session_id, req.message, db)
        
        if reply_data.get("is_complete"):
            stmt = select(ChatSession).where(ChatSession.session_id == req.session_id)
            result = await db.execute(stmt)
            chat_session = result.scalar_one()
            
            background_tasks.add_task(run_post_chat, req.session_id, chat_session.state)
            
        return reply_data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Chat message error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/status/{session_id}")
async def chat_status(session_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(ChatSession).where(ChatSession.session_id == session_id)
    result = await db.execute(stmt)
    chat_session = result.scalar_one_or_none()
    
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    return {
        "score": chat_session.score,
        "email_sent": chat_session.email_sent,
        "appt_booked": chat_session.appt_booked,
        "sheet_saved": chat_session.sheet_row is not None,
        "summary": chat_session.state.get("summary")
    }
