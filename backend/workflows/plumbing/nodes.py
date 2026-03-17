import time
import structlog
import asyncio
from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage
from llm import llm
from core.tool_executor import tool_executor
from tools.email import email_tool
from tools.sheets import sheets_tool
from tools.sms import sms_tool
from core.database import Lead, get_db_context
from workflows.base import (
    field_missing, merge_extracted, parse_json, build_lc_messages, 
    last_user_msg, get_appt_slots, rule_score_lead
)
from workflows.plumbing.prompts import PLUMBING_EXPERT_SYSTEM, EXTRACT_FIELDS_SYSTEM

logger = structlog.get_logger(__name__)

async def node_check_complete(state: dict) -> dict:
    required = ["name", "email", "issue", "phone"]
    has_required = all(not field_missing(state, f) for f in required)
    if has_required or int(state.get("turn_count", 0)) >= 8:
        state["is_complete"] = True
    return state

async def node_extract_fields(state: dict) -> dict:
    start = time.perf_counter()
    msg = last_user_msg(state)
    if msg:
        try:
            resp = await llm.ainvoke([SystemMessage(content=EXTRACT_FIELDS_SYSTEM), HumanMessage(content=msg)])
            extracted = parse_json(resp.content)
            if extracted: merge_extracted(state, extracted)
        except Exception as e: logger.error("extract_failed", error=str(e))
    logger.info("node_complete", node="plumb_extract", duration_ms=int((time.perf_counter()-start)*1000))
    return state

async def node_chat_reply(state: dict) -> dict:
    start = time.perf_counter()
    try:
        slots = state.get("appt_slots") or get_appt_slots()
        state["appt_slots"] = slots
        messages = [SystemMessage(content=PLUMBING_EXPERT_SYSTEM.format(slot_1=slots[0], slot_2=slots[1], slot_3=slots[2]))]
        messages += build_lc_messages(state)
        resp = await llm.ainvoke(messages)
        state.setdefault("messages", []).append({"role": "assistant", "content": resp.content, "ts": datetime.utcnow().isoformat()})
        state["turn_count"] = int(state.get("turn_count", 0)) + 1
    except Exception as e: logger.error("chat_reply_failed", error=str(e))
    logger.info("node_complete", node="plumb_reply", duration_ms=int((time.perf_counter()-start)*1000))
    return state

async def node_save_and_email(state: dict) -> dict:
    start = time.perf_counter()
    state["vertical"] = "plumbing"
    state.update(rule_score_lead(state))
    
    try:
        async with get_db_context() as db:
            lead = Lead(
                name=state.get("name"),
                email=state.get("email"),
                phone=state.get("phone"),
                issue=state.get("issue"),
                vertical="plumbing",
                session_id=state.get("session_id")
            )
            db.add(lead)
            await db.commit()
    except Exception as e:
        logger.error("db_save_failed", error=str(e))
    
    tasks = [
        tool_executor.execute("sheets", sheets_tool.save_lead_to_sheet, row=[
            datetime.utcnow().isoformat(),
            state.get("name", "N/A"),
            state.get("email", "N/A"),
            state.get("phone", "N/A"),
            state.get("issue", "N/A"),
            state.get("score_reason", "N/A"),
            state.get("session_id", "N/A")
        ])
    ]
    
    if state.get("email"):
        html = f"<h3>Plumbing Service Summary</h3><p>Hi {state.get('name')}, we have your request. Our team will contact you shortly.</p>"
        tasks.append(tool_executor.execute("resend", email_tool.send_email, to=state.get("email"), subject="Plumbing Service Summary", html=html))

    if state.get("urgency") == "emergency" and state.get("phone"):
        tasks.append(tool_executor.execute("sms", sms_tool.send_sms, to=state.get("phone"), body="Emergency Plumber Dispatched. Please keep your main water valve shut."))
    
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("node_complete", node="plumb_save", duration_ms=int((time.perf_counter()-start)*1000))
    return state