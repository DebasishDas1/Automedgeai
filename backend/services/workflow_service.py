# services/workflow_service.py
# LangGraph chat session management — SQLAlchemy AsyncSession version.
# ChatSession ORM model mirrors the uploaded database.py exactly.
import json
import logging
import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import ChatSession, get_db_context
from workflows.hvac.graph         import hvac_chat_graph, hvac_post_chat_graph
from workflows.pest_control.graph import pest_chat_graph, pest_post_chat_graph
from workflows.plumbing.graph     import plumbing_chat_graph, plumbing_post_chat_graph
from workflows.roofing.graph      import roofing_chat_graph, roofing_post_chat_graph

logger = logging.getLogger(__name__)

_CHAT_GRAPHS = {
    "hvac":         hvac_chat_graph,
    "pest_control": pest_chat_graph,
    "plumbing":     plumbing_chat_graph,
    "roofing":      roofing_chat_graph,
}
_POST_CHAT_GRAPHS = {
    "hvac":         hvac_post_chat_graph,
    "pest_control": pest_post_chat_graph,
    "plumbing":     plumbing_post_chat_graph,
    "roofing":      roofing_post_chat_graph,
}
_COLLECTIBLE_FIELDS = [
    "name", "email", "phone", "city", "issue",
    "pest_type", "damage_type", "issue_type",
    "urgency", "is_homeowner", "property_type",
    "appt_booked", "appt_confirmed",
]


# ── DB helpers ────────────────────────────────────────────────────────────────

async def _load_session(db: AsyncSession, session_id: str) -> ChatSession | None:
    result = await db.execute(
        select(ChatSession).where(ChatSession.session_id == session_id)
    )
    return result.scalar_one_or_none()


async def _save_session(db: AsyncSession, row: ChatSession, state: dict) -> None:
    # Strip internal routing key — never persisted
    clean_state = {k: v for k, v in state.items() if k != "_vertical"}
    row.state       = clean_state
    row.score       = state.get("score")
    row.sheet_row   = state.get("sheet_row")
    row.sheet_tab   = state.get("sheet_tab")
    row.email_sent  = bool(state.get("email_sent"))
    row.appt_booked = bool(state.get("appt_booked"))
    row.is_complete = bool(state.get("is_complete"))
    row.updated_at  = datetime.utcnow()
    await db.commit()
    await db.refresh(row)


# ── Public API ────────────────────────────────────────────────────────────────

async def start_session(
    db:       AsyncSession,
    vertical: str,
    source:   str | None = None,
    metadata: dict | None = None,
) -> dict:
    session_id = str(uuid.uuid4())
    initial_state: dict = {
        "session_id":  session_id,
        "vertical":    vertical,
        "messages":    [],
        "turn_count":  0,
        "is_complete": False,
        "appt_booked": False,
        "source":      source,
        **(metadata or {}),
    }

    # Persist before running graph — safe if graph throws
    row = ChatSession(
        session_id  = session_id,
        vertical    = vertical,
        state       = initial_state,
        is_complete = False,
        appt_booked = False,
        email_sent  = False,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)

    logger.info(f"Session started: {session_id} vertical={vertical}")
    return {
        "session_id": session_id,
        "vertical":   vertical,
        "turn": 0,
    }


async def send_message(
    db: AsyncSession,
    session_id: str,
    user_msg: str,
) -> dict:
    row = await _load_session(db, session_id)
    if row is None:
        raise ValueError(f"Session not found: {session_id}")
    if row.is_complete:
        raise ValueError(f"Session already complete: {session_id}")

    vertical = row.vertical
    state = dict(row.state)

    msg = user_msg.strip().lower()

    # ── Fast path (no LLM) ─────────────────────

    # simple greeting detection
    if msg in {"hi", "hello", "hey"} and state.get("turn_count", 0) > 0:
        return {
            "session_id": session_id,
            "message": "Hello again! How can I help with your issue?",
            "turn": state.get("turn_count", 0),
            "is_complete": False,
            "appt_booked": False,
            "fields_collected": {},
        }

    # detect phone number
    if "phone" not in state and any(c.isdigit() for c in msg) and len(msg) >= 10:
        state["phone"] = msg
        state.setdefault("messages", []).append({
            "role": "user",
            "content": user_msg,
            "ts": datetime.utcnow().isoformat(),
        })
        state["turn_count"] = state.get("turn_count", 0) + 1

        await _save_session(db, row, state)

        return {
            "session_id": session_id,
            "message": "Got it 👍 What's your city?",
            "turn": state["turn_count"],
            "is_complete": False,
            "appt_booked": False,
            "fields_collected": {"phone": msg},
        }

    # ── Default: run LangGraph ─────────────────

    state.setdefault("messages", []).append({
        "role": "user",
        "content": user_msg,
        "ts": datetime.utcnow().isoformat(),
    })

    result = _CHAT_GRAPHS[vertical].invoke(state)
    result["_vertical"] = vertical

    await _save_session(db, row, result)

    messages = result.get("messages", [])
    last_ai = next(
        (m["content"] for m in reversed(messages) if m.get("role") == "assistant"),
        "",
    )

    fields_collected = {
        k: result[k] for k in _COLLECTIBLE_FIELDS if result.get(k) is not None
    }

    return {
        "session_id": session_id,
        "message": last_ai,
        "turn": result.get("turn_count", 0),
        "is_complete": bool(result.get("is_complete")),
        "appt_booked": bool(result.get("appt_booked")),
        "fields_collected": fields_collected,
        "_state": result,
        "_vertical": vertical,
    }



async def run_post_chat(state: dict, vertical: str) -> None:
    """Background task — runs once when chat ends. Uses its own DB session."""
    session_id = state.get("session_id", "unknown")
    logger.info(f"post-chat starting: session={session_id} vertical={vertical}")
    try:
        result = _POST_CHAT_GRAPHS[vertical].invoke(state)
        logger.info(
            f"post-chat done: session={session_id} "
            f"score={result.get('score')} email={result.get('email_sent')} "
            f"sheet_row={result.get('sheet_row')}"
        )
        # Persist final post-chat state
        async with get_db_context() as db:
            row = await _load_session(db, session_id)
            if row:
                await _save_session(db, row, result)
    except Exception as e:
        logger.error(f"post-chat failed: session={session_id} error={e}")
        # Never raise — background task, caller already responded