import structlog
import uuid
import asyncio
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import ChatSession, get_db_context
from workflows.registry import registry

logger = structlog.get_logger(__name__)

async def _save_session(db: AsyncSession, row: ChatSession, state: dict) -> None:
    # State trimming logic (per-request isolation preserved)
    state["messages"] = state.get("messages", [])[-10:]
    row.state = {k: v for k, v in state.items() if not k.startswith("_")}
    row.is_complete = bool(state.get("is_complete"))
    row.updated_at = datetime.utcnow()
    # No manual commit() here; transaction is managed at the request level or context floor
    # and committed at handle_message/run_post_chat completion.

async def start_session(db: AsyncSession, vertical: str) -> dict:
    session_id = str(uuid.uuid4())
    row = ChatSession(session_id=session_id, vertical=vertical, state={"messages": []})
    db.add(row)
    await db.commit()
    logger.info("session_started", session_id=session_id, vertical=vertical)
    return {"session_id": session_id, "vertical": vertical}

async def send_message(db: AsyncSession, session_id: str, user_msg: str) -> dict:
    # RACE CONDITION FIX: Use FOR UPDATE to lock the row during the LLM turn
    # This ensures two concurrent messages for the same session are processed sequentially.
    stmt = select(ChatSession).where(ChatSession.session_id == session_id).with_for_update()
    res = await db.execute(stmt)
    row = res.scalar_one_or_none()
    
    if not row or row.is_complete: 
        raise ValueError("invalid_session")

    # Create a local copy to avoid cross-request contamination
    state = dict(row.state)
    state.setdefault("messages", []).append({
        "role": "user", 
        "content": user_msg, 
        "ts": datetime.utcnow().isoformat()
    })
    
    graph = registry.get_chat_graph(row.vertical)
    # Graph execution (LangGraph ainvoke is safe for concurrent sessions)
    result = await graph.ainvoke(state)
    
    await _save_session(db, row, result)
    await db.commit() # Release the row lock

    if result.get("is_complete"):
        asyncio.create_task(run_post_chat(result, row.vertical))

    last_ai = next((m["content"] for m in reversed(result.get("messages", [])) if m.get("role") == "assistant"), "")
    return {"session_id": session_id, "message": last_ai, "is_complete": bool(result.get("is_complete"))}

async def run_post_chat(state: dict, vertical: str) -> None:
    graph = registry.get_post_graph(vertical)
    if not graph: return
    try:
        async with get_db_context() as db:
            # Re-lock for post-chat updates
            stmt = select(ChatSession).where(ChatSession.session_id == state["session_id"]).with_for_update()
            res = await db.execute(stmt)
            row = res.scalar_one_or_none()
            
            if row:
                result = await graph.ainvoke(state)
                await _save_session(db, row, result)
                await db.commit()
    except Exception as e:
        logger.error("post_chat_failed", session=state.get("session_id"), error=str(e))