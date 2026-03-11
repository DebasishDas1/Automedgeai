# services/workflow_service.py
# LangGraph chat session management — SQLAlchemy AsyncSession version.
# ChatSession ORM model mirrors the uploaded database.py exactly.
import logging
import uuid
import asyncio
from datetime import datetime

from sqlalchemy import select
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
    # Remove internal routing keys
    clean_state = {k: v for k, v in state.items() if not k.startswith("_")}

    row.state       = clean_state
    row.score       = state.get("score")
    row.sheet_row   = state.get("sheet_row")
    row.sheet_tab   = state.get("sheet_tab")
    row.email_sent  = bool(state.get("email_sent"))
    row.appt_booked = bool(state.get("appt_booked"))
    row.is_complete = bool(state.get("is_complete"))
    row.updated_at  = datetime.utcnow()

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        logger.exception("DB commit failed while saving chat session")
        raise

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
        "turn":       0,
    }


async def send_message(
    db:         AsyncSession,
    session_id: str,
    user_msg:   str,
) -> dict:
    row = await _load_session(db, session_id)
    if row is None:
        raise ValueError(f"Session not found: {session_id}")
    if row.is_complete:
        raise ValueError(f"Session already complete: {session_id}")

    vertical = row.vertical
    state    = dict(row.state)   # JSONB → dict

    # Append user message
    state.setdefault("messages", []).append({
        "role":    "user",
        "content": user_msg,
        "ts":      datetime.utcnow().isoformat(timespec="seconds"),
    })

    result = _CHAT_GRAPHS[vertical].invoke(state)
    result["_vertical"] = vertical
    await _save_session(db, row, result)

    # trigger background workflow once
    if result.get("is_complete") and not row.is_complete:
        asyncio.create_task(
            run_post_chat(result, vertical)
        )

    messages = result.get("messages", [])
    last_ai  = next(
        (m["content"] for m in reversed(messages) if m.get("role") == "assistant"), ""
    )
    fields_collected = {
        k: result[k] for k in _COLLECTIBLE_FIELDS if result.get(k) is not None
    }
    logger.info(
        f"turn={result.get('turn_count')} session={session_id} "
        f"complete={result.get('is_complete')}"
    )
    return {
        "session_id":       session_id,
        "message":          last_ai,
        "turn":             result.get("turn_count", 0),
        "is_complete":      bool(result.get("is_complete")),
        "appt_booked":      bool(result.get("appt_booked")),
        "fields_collected": fields_collected,
        "_state":           result,
        "_vertical":        vertical,
    }


async def run_post_chat(state: dict, vertical: str) -> None:
    """Background task — runs once when chat ends."""

    session_id = state.get("session_id", "unknown")
    logger.info(f"post-chat starting: session={session_id} vertical={vertical}")

    graph = _POST_CHAT_GRAPHS.get(vertical)

    if not graph:
        logger.error(f"No post-chat graph registered for vertical={vertical}")
        return

    try:
        result = graph.invoke(state)

        logger.info(
            f"post-chat finished session={session_id} "
            f"score={result.get('score')} "
            f"email_sent={result.get('email_sent')} "
            f"sheet_row={result.get('sheet_row')}"
        )

        async with get_db_context() as db:

            row = await _load_session(db, session_id)

            if row:
                await _save_session(db, row, result)

            # Import here to avoid circular imports
            from services.lead_service import upsert_from_chat

            await upsert_from_chat(db, session_id, result)

    except Exception:
        logger.exception(f"post-chat failed for session={session_id}")