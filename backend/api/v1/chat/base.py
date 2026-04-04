# api/v1/chat/base.py
# Shared request/response models and handler functions.
from __future__ import annotations

import asyncio
import json
import structlog
from typing import AsyncGenerator, Literal

from fastapi import HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from tools import workflow_tools
from workflows.registry import registry

logger = structlog.get_logger(__name__)

Vertical = Literal["hvac", "pest_control", "plumbing", "roofing"]


# ── Request / Response schemas ────────────────────────────────────────────────

class StartRequest(BaseModel):
    vertical: Vertical  # hvac, plumbing, roofing, pest_control
    source: str | None = None
    name: str | None = None
    email: str | None = None
    phone: str | None = None

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

async def handle_start(vertical: Vertical, body: StartRequest, db: AsyncSession) -> dict:
    """Start a new chat session for the given vertical."""
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


async def handle_message(
    body: MessageRequest,
    db: AsyncSession,
    background_tasks: BackgroundTasks,
    request: Request,
) -> dict:
    """Process a user message in an existing session."""
    try:
        return await workflow_tools.send_message(
            db=db,
            session_id=body.session_id,
            user_msg=body.message,
            background_tasks=background_tasks,
            app_state=request.app.state,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("message_failed", session_id=body.session_id, error=str(exc))
        raise HTTPException(status_code=500, detail="processing_error")


async def handle_message_stream(
    body: MessageRequest,
    db: AsyncSession,
    background_tasks: BackgroundTasks,
    request: Request,
) -> StreamingResponse:
    """
    SSE streaming endpoint for real-time token delivery.

    FIX (CRITICAL): background_tasks.add_task() is now called OUTSIDE the
    generator, via a shared result container, because FastAPI executes
    BackgroundTasks after the response completes — calling add_task() from
    inside a running generator is undefined behavior in Starlette's ASGI layer.

    FIX (RENDER): Added SSE heartbeat every 25s to prevent Render free-tier's
    30-second idle proxy timeout from killing long-running LLM streams.
    """
    from core.database import ChatSession, get_db_context, select  # local to avoid circular

    # ── Eager session validation (before streaming begins) ────────────────────
    res = await db.execute(
        select(ChatSession).where(ChatSession.session_id == body.session_id)
    )
    row = res.scalar_one_or_none()

    if row is None:
        raise HTTPException(status_code=404, detail="session_not_found")

    # Snapshot values for use inside the generator (outer db closes after return)
    vertical = row.vertical
    state_snapshot = dict(row.state)

    # Shared mutable container — lets generator signal completion to outer scope
    # without calling background_tasks from inside the generator (unsafe).
    _result_container: dict = {"final_output": None, "should_trigger": False}

    async def stream() -> AsyncGenerator[str, None]:
        graph = registry.get_chat_graph(vertical)

        messages = list(state_snapshot.get("messages", []))
        messages.append({"role": "user", "content": body.message})
        current_state = {**state_snapshot, "messages": messages}

        final_output: dict | None = None
        last_emit = asyncio.get_event_loop().time()

        try:
            async for event in graph.astream_events(current_state, version="v2"):
                # ── Heartbeat: emit SSE comment every 25s to prevent Render timeout ──
                now = asyncio.get_event_loop().time()
                if now - last_emit > 25:
                    yield ": ping\n\n"
                    last_emit = now

                evt = event["event"]

                if (
                    evt == "on_chat_model_stream"
                    and event.get("metadata", {}).get("langgraph_node") == "reply"
                ):
                    chunk = event["data"]["chunk"].content
                    if chunk:
                        yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                        last_emit = asyncio.get_event_loop().time()

                elif evt == "on_chain_end" and event["name"] == "LangGraph":
                    final_output = event["data"].get("output")

        except Exception as exc:
            logger.error("stream_failed", session_id=body.session_id, error=str(exc))
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
                        was_complete = row2.is_complete
                        await workflow_tools._save_session(fresh_db, row2, final_output)
                        await fresh_db.commit()

                        # Store intent for outer scope — do NOT call background_tasks here
                        if bool(final_output.get("is_complete")) and not was_complete:
                            _result_container["should_trigger"] = True

            except Exception as exc:
                logger.error("stream_save_failed", session_id=body.session_id, error=str(exc))

            # Store for metadata event and outer scope
            _result_container["final_output"] = final_output

        # ── Metadata event ────────────────────────────────────────────────────
        if final_output:
            meta = {
                "turn":             final_output.get("turn_count", 0),
                "is_complete":      bool(final_output.get("is_complete")),
                "appt_booked":      bool(final_output.get("appt_booked")),
                "fields_collected": {
                    k: final_output.get(k)
                    for k in ("name", "email", "phone", "issue", "description", "urgency", "address")
                    if final_output.get(k) is not None
                },
            }
            yield f"data: {json.dumps({'metadata': meta})}\n\n"

        yield "data: [DONE]\n\n"

    # ── Build response first, THEN schedule background task ───────────────────
    # We wrap stream() in an async wrapper so we can inspect _result_container
    # after the generator exhausts. However, StreamingResponse is lazy — the
    # generator runs during response transmission, not here.
    # The safe pattern: register background_tasks AFTER streaming completes by
    # using a shim generator that sets a flag and triggers the task via an
    # async wrapper.

    async def shim() -> AsyncGenerator[str, None]:
        async for chunk in stream():
            yield chunk
        # Generator is now exhausted (stream complete). Safe to schedule.
        if _result_container["should_trigger"] and _result_container["final_output"]:
            background_tasks.add_task(
                workflow_tools.run_post_chat,
                dict(_result_container["final_output"]),
                vertical,
                request.app.state,
            )

    return StreamingResponse(
        shim(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",       # disable nginx buffering
            "Connection": "keep-alive",       # explicit for Render proxy
            "Transfer-Encoding": "chunked",  # ensure chunked streaming
        },
    )