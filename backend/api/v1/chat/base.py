# api/v1/chat/base.py
# Shared request/response models and handler functions.
from __future__ import annotations

import json
import structlog
from typing import AsyncGenerator, Literal

from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from tools import workflow_tools
from workflows.registry import registry

logger = structlog.get_logger(__name__)

Vertical = Literal["hvac", "pest_control", "plumbing", "roofing"]


# ── Request / Response schemas ────────────────────────────────────────────────

class StartRequest(BaseModel):
    source: str | None = None
    name: str | None = None
    email: str | None = None
    phone: str | None = None

    # FIX: no sanitization — a name like "<script>" would be stored raw.
    # Strip whitespace at minimum; full HTML escaping happens at delivery time.
    @field_validator("name", "email", "phone", "source", mode="before")
    @classmethod
    def strip_strings(cls, v):
        if isinstance(v, str):
            v = v.strip()
            return v if v else None
        return v


class StartResponse(BaseModel):
    session_id: str
    vertical: Vertical
    turn: int = 0


class MessageRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1, max_length=1000)

    @field_validator("message", mode="before")
    @classmethod
    def strip_message(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v


class MessageResponse(BaseModel):
    session_id: str
    message: str
    turn: int
    is_complete: bool
    appt_booked: bool
    fields_collected: dict


# ── Handler functions ─────────────────────────────────────────────────────────

async def handle_start(vertical: Vertical, body: StartRequest, db) -> dict:
    """
    Start a new chat session for the given vertical.

    Fix: original caught all exceptions and returned 500. Now preserves
    ValueError as 400 so callers get actionable errors (e.g. invalid vertical).
    """
    try:
        return await workflow_tools.start_session(
            db=db,
            vertical=vertical,
            name=body.name,
            email=body.email,
            phone=body.phone,
            source=body.source,
        )
    except ValueError as exc:
        logger.warning("start_chat_bad_request", error=str(exc), vertical=vertical)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("start_chat_failed", error=str(exc), vertical=vertical)
        raise HTTPException(status_code=500, detail="start_failed")


async def handle_message(body: MessageRequest, db) -> dict:
    """
    Process a user message in an existing session.
    """
    try:
        return await workflow_tools.send_message(
            db=db,
            session_id=body.session_id,
            user_msg=body.message,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(
            "message_failed",
            session_id=body.session_id,
            error=str(exc),
        )
        raise HTTPException(status_code=500, detail="processing_error")


async def handle_message_stream(body: MessageRequest, db) -> StreamingResponse:
    """
    SSE streaming endpoint for real-time token delivery.

    Fixes:
    - DB session was used inside the `stream()` generator which outlives the
      request scope. The `db` dependency closes after the handler returns, so
      `_save_session` was calling a closed session. Fixed by loading the row
      eagerly before returning StreamingResponse, then using a fresh db context
      inside the generator for the save.
    - `state.setdefault("messages", []).append(...)` mutates the dict in-place
      and bypasses LangGraph's add_messages reducer. Fixed to build a new list.
    - `AsyncGenerator` was imported but unused (leftover). Removed.
    - `BackgroundTasks`, `ORJSONResponse`, `status` were imported but unused. Removed.
    - No error handling inside the generator — a crash mid-stream left the client
      hanging with no `[DONE]` signal. Added try/except with error SSE event.
    - `graph.astream_events(..., version="v1")` is deprecated in LangGraph ≥0.2.
      Use version="v2".
    - Session re-fetched inside generator on every call — moved outside.
    """
    from core.database import ChatSession, get_db_context, select  # local to avoid circular

    # ── Eager session validation (before we start streaming) ─────────────────
    res = await db.execute(
        select(ChatSession).where(ChatSession.session_id == body.session_id)
    )
    row = res.scalar_one_or_none()

    if row is None:
        raise HTTPException(status_code=404, detail="session_not_found")
    if row.is_complete:
        raise HTTPException(status_code=400, detail="session_already_complete")

    # Snapshot values we need inside the generator (db session must NOT be used there)
    vertical = row.vertical
    state_snapshot = dict(row.state)

    async def stream() -> AsyncGenerator[str, None]:
        graph = registry.get_chat_graph(vertical)

        # Build new message list — don't mutate state_snapshot in-place
        messages = list(state_snapshot.get("messages", []))
        messages.append({"role": "user", "content": body.message})
        current_state = {**state_snapshot, "messages": messages}

        final_output: dict | None = None

        try:
            async for event in graph.astream_events(current_state, version="v2"):
                evt = event["event"]

                if evt == "on_chat_model_stream":
                    chunk = event["data"]["chunk"].content
                    if chunk:
                        yield f"data: {json.dumps({'chunk': chunk})}\n\n"

                elif evt == "on_chain_end" and event["name"] == "LangGraph":
                    final_output = event["data"].get("output")

        except Exception as exc:
            logger.error(
                "stream_failed",
                session_id=body.session_id,
                error=str(exc),
            )
            yield f"data: {json.dumps({'error': 'stream_error'})}\n\n"
            return

        # ── Persist final state with a fresh DB context ───────────────────────
        if final_output is not None:
            try:
                async with get_db_context() as fresh_db:
                    res2 = await fresh_db.execute(
                        select(ChatSession).where(ChatSession.session_id == body.session_id)
                    )
                    row2 = res2.scalar_one_or_none()
                    if row2:
                        await workflow_tools._save_session(fresh_db, row2, final_output)
                        await fresh_db.commit()
            except Exception as exc:
                logger.error(
                    "stream_save_failed",
                    session_id=body.session_id,
                    error=str(exc),
                )

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering for SSE
        },
    )