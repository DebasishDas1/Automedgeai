from __future__ import annotations

import asyncio
import uuid
import structlog
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from fastapi import BackgroundTasks
from core.database import ChatSession, get_db_context
from workflows.registry import registry

logger = structlog.get_logger(__name__)


async def _save_session(db: AsyncSession, row: ChatSession, state: dict[str, Any]) -> None:
    """Normalize and persist LangGraph state. Caller must commit."""
    if isinstance(state, str):
        state = {"messages": [{"role": "assistant", "content": state}], "is_complete": False}
    elif hasattr(state, "state"):
        state = dict(state.state)
    elif not isinstance(state, dict):
        state = {"messages": [{"role": "assistant", "content": str(state)}], "is_complete": False}

    msgs = state.get("messages", [])
    if not isinstance(msgs, list):
        msgs = [msgs]
    state["messages"] = msgs[-20:]

    row.state = {k: v for k, v in state.items() if not k.startswith("_")}
    flag_modified(row, "state")
    row.is_complete = bool(state.get("is_complete"))
    row.updated_at = datetime.now(timezone.utc)


async def start_session(
    db: AsyncSession,
    vertical: str,
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    source: str | None = None,
) -> dict:
    """
    Create a new chat session, pre-seeding contact fields from the lead form.
    """
    _SUPPORTED = {"hvac", "plumbing", "roofing", "pest_control"}
    if vertical not in _SUPPORTED:
        raise ValueError(f"Unknown vertical '{vertical}'. Supported: {sorted(_SUPPORTED)}")

    session_id = str(uuid.uuid4())
    initial_state = {
        "session_id":   session_id,
        "vertical":     vertical,
        "messages":     [],
        "turn_count":   0,
        "is_complete":  False,
        "is_spam":      False,
        "intent":       "service_request",
        "name":         name  or None,
        "email":        email or None,
        "phone":        phone or None,
        "issue":        None,
        "description":  None,
        "urgency":      None,
        "address":      None,
        "is_homeowner": None,
        "ai_urgency":   None,
    }

    row = ChatSession(
        session_id=session_id,
        vertical=vertical,
        state=initial_state,
        form_data={"name": name, "email": email, "phone": phone, "source": source},
    )
    db.add(row)
    await db.commit()
    logger.info("session_started", session_id=session_id, vertical=vertical)
    return {"session_id": session_id, "vertical": vertical, "turn": 0}


async def send_message(
    db: AsyncSession, 
    session_id: str, 
    user_msg: str, 
    background_tasks: BackgroundTasks,
    app_state: Any = None
) -> dict:
    """
    Append user message, invoke chat graph, persist result.

    FIX (CRITICAL): Re-fetch with lock ONLY after the slow LLM call returns.
    Held locks during graph.ainvoke() cause deadlocks and worker pool exhaustion.
    """
    # 1. READ ONLY - No lock held during slow AI call
    stmt = select(ChatSession).where(ChatSession.session_id == session_id)
    res = await db.execute(stmt)
    row = res.scalar_one_or_none()

    if row is None:
        raise ValueError("session_not_found")

    state = dict(row.state)
    # Expunge to ensure the next fetch with_for_update hits the DB, not the cache
    db.expunge(row)

    graph_input = {
        **state,
        "messages": list(state.get("messages", [])) + [{
            "role": "user",
            "content": user_msg,
            "ts": datetime.now(timezone.utc).isoformat(),
        }],
    }

    graph = registry.get_chat_graph(row.vertical)
    result = await graph.ainvoke(graph_input)

    # 2. WRITE LOCK - Only for the millisecond it takes to update the row
    stmt_lock = select(ChatSession).where(
        ChatSession.session_id == session_id
    ).with_for_update()
    res_lock = await db.execute(stmt_lock)
    row_locked = res_lock.scalar_one_or_none()
    
    if not row_locked:
        # Extreme edge case: session deleted during AI call
        raise ValueError("session_lost_during_ai_call")

    was_complete = bool(row_locked.is_complete)
    await _save_session(db, row_locked, result)
    await db.commit()

    if result.get("is_complete") and not was_complete:
        background_tasks.add_task(
            run_post_chat, 
            dict(result), 
            row_locked.vertical,
            app_state
        )

    last_ai = next(
        (m["content"] for m in reversed(result.get("messages", []))
         if m.get("role") == "assistant"),
        "",
    )
    return {
        "session_id":       session_id,
        "message":          last_ai,
        "turn":             result.get("turn_count", 0),
        "is_complete":      bool(result.get("is_complete")),
        "appt_booked":      bool(result.get("appt_booked")),
        "fields_collected": {
            k: result.get(k)
            for k in ("name", "email", "phone", "issue", "description", "urgency", "address")
            if result.get(k) is not None
        },
    }


async def run_post_chat(state: dict, vertical: str, app_state: Any = None) -> None:
    """Run score + deliver post-chat graph. Errors are fully caught."""
    graph = registry.get_post_graph(vertical)
    if graph is None:
        logger.warning("post_chat_no_graph", vertical=vertical)
        return

    session_id = state.get("session_id")
    try:
        async with get_db_context() as db:
            stmt = select(ChatSession).where(
                ChatSession.session_id == session_id
            ).with_for_update()
            res = await db.execute(stmt)
            row = res.scalar_one_or_none()
            if row is None:
                logger.warning("post_chat_session_not_found", session_id=session_id)
                return
            
            # Pass app_state in the state strictly for the duration of this run.
            # It will be filtered out during DB persistence by _save_session (startswith "_").
            if app_state:
                state["_app_state"] = app_state
            
            result = await graph.ainvoke(state)
            await _save_session(db, row, result)
            await db.commit()
            logger.info("post_chat_complete", session_id=session_id)
    except Exception as exc:
        logger.error(
            "post_chat_failed",
            session_id=session_id[:20] if session_id else "unknown",
            error_type=type(exc).__name__,
        )


async def save_session_by_id(db: AsyncSession, session_id: str, state: dict) -> None:
    """Update session state by ID. Caller must commit."""
    res = await db.execute(
        select(ChatSession).where(ChatSession.session_id == session_id)
    )
    row = res.scalar_one_or_none()
    if row is None:
        raise ValueError(f"session_not_found: {session_id}")
    await _save_session(db, row, state)