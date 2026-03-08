import json
import logging
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import ChatSession, AsyncSessionLocal
from models.workflow import HVACChatState

# Graphs
from workflows.hvac.graph import hvac_chat_graph, post_hvac_chat_graph
from workflows.roofing.graph import roofing_graph
from workflows.plumbing.graph import plumbing_graph
from workflows.pest_control.graph import pest_graph

logger = logging.getLogger(__name__)


# Graph registry
GRAPHS = {
    "hvac": hvac_chat_graph,
    "roofing": roofing_graph,
    "plumbing": plumbing_graph,
    "pest_control": pest_graph,
}


class WorkflowService:

    @staticmethod
    async def stream_workflow(vertical: str, state: dict) -> AsyncGenerator[str, None]:
        graph = GRAPHS.get(vertical)

        if not graph:
            yield WorkflowService._sse("error", f"Unknown vertical: {vertical}")
            return

        try:
            async for event in graph.astream(state):

                for updates in event.values():
                    events = updates.get("events")

                    if events:
                        yield WorkflowService._sse("event", events[-1])

            yield WorkflowService._sse("complete", "Workflow finished")

        except Exception as e:
            logger.exception("Workflow stream failed")
            yield WorkflowService._sse("error", str(e))

    @staticmethod
    def _sse(event_type: str, data):
        return f"data: {json.dumps({'type': event_type, 'data': data})}\n\n"


workflow_service = WorkflowService()


# ---------------------------------------------
# CHAT WORKFLOW
# ---------------------------------------------

async def run_chat_turn(
    session_id: str,
    user_message: str,
    db: AsyncSession
) -> dict:

    stmt = select(ChatSession).where(ChatSession.session_id == session_id)
    result = await db.execute(stmt)

    chat_session = result.scalar_one_or_none()

    if not chat_session:
        raise ValueError("Session not found")

    state = chat_session.state or {}

    # ensure messages list
    state.setdefault("messages", [])

    state["messages"].append({
        "role": "user",
        "content": user_message,
        "ts": datetime.utcnow().isoformat()
    })

    # Run graph asynchronously
    new_state = await hvac_chat_graph.ainvoke(state)

    # Extract assistant reply
    ai_reply = ""

    messages = new_state.get("messages", [])
    if messages and messages[-1].get("role") == "assistant":
        ai_reply = messages[-1].get("content", "")

    chat_session.state = new_state

    await db.commit()

    return {
        "message": ai_reply,
        "turn": new_state.get("turn_count", 0),
        "is_complete": new_state.get("is_complete", False),
        "appt_booked": new_state.get("appt_booked", False),
        "fields_collected": {
            k: new_state.get(k)
            for k in ["name", "email", "phone", "issue", "location"]
        }
    }


# ---------------------------------------------
# POST CHAT WORKFLOW
# ---------------------------------------------

async def run_post_chat(session_id: str, state: HVACChatState) -> None:

    try:
        final_state = await post_hvac_chat_graph.ainvoke(state)

        async with AsyncSessionLocal() as db:

            stmt = select(ChatSession).where(ChatSession.session_id == session_id)
            result = await db.execute(stmt)

            chat_session = result.scalar_one()

            chat_session.score = final_state.get("score")
            chat_session.sheet_row = final_state.get("sheet_row")
            chat_session.sheet_tab = final_state.get("sheet_tab")
            chat_session.email_sent = final_state.get("email_sent", False)
            chat_session.appt_booked = final_state.get("appt_booked", False)
            chat_session.is_complete = True
            chat_session.state = final_state

            await db.commit()

            logger.info(
                f"Session {session_id} complete | "
                f"score={chat_session.score} | "
                f"sheet={chat_session.sheet_tab}:{chat_session.sheet_row} | "
                f"email={chat_session.email_sent}"
            )

    except Exception as e:
        logger.exception(f"run_post_chat failed for {session_id}")