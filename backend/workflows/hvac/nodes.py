# workflows/hvac/nodes.py
# HVAC graph node functions.
#
# Optimizations vs original:
#  1. All helpers imported from workflows/base.py — no duplication
#  2. node_score_lead uses rule_score_lead() — zero LLM tokens
#  3. node_generate_summary makes ONE LLM call (was two) — saves ~300t
#  4. node_extract_fields only runs appointment check when slots are shown
#     AND last user msg looks like a confirmation (keyword pre-filter)
#  5. node_extract_final skips if all required fields already collected
#  6. EXTRACT_FIELDS_SYSTEM trimmed 275t, APPOINTMENT_CONFIRM 254t
#  7. llm imported from llm module (max_tokens enforced)
import json
import logging
from datetime import datetime

from langchain_core.messages import SystemMessage, HumanMessage

from llm import llm
from core.config import settings
from workflows.base import (
    field_missing,
    merge_extracted,
    parse_json,
    build_lc_messages,
    last_user_msg,
    full_transcript,
    get_appt_slots,
    rule_score_lead,
)
from workflows.hvac.prompts import (
    HVAC_EXPERT_SYSTEM,
    FIELD_COLLECTION_GUIDE,
    EXTRACT_FIELDS_SYSTEM,
    APPOINTMENT_CONFIRM_SYSTEM,
    SUMMARY_COMBINED_SYSTEM,
)
from tools.email import email_tool
from tools.sheets import sheets_tool

logger = logging.getLogger(__name__)

# Fields that must be present for the chat to be considered complete
_REQUIRED = ["name", "email", "phone", "issue", "location"]

# Natural conversation order — one field per turn
_FIELD_PRIORITY = ["issue", "urgency", "is_homeowner", "location", "name", "phone", "email", "system_age"]

# Keywords that suggest a user is confirming an appointment slot
# Used as a cheap pre-filter before spending tokens on APPOINTMENT_CONFIRM
_CONFIRM_SIGNALS = {
    "option", "number", "slot", "works", "perfect", "great", "sure",
    "yes please", "sounds good", "let's do", "lets do", "that one",
    "morning", "afternoon", "pm", "am", "monday", "tuesday", "wednesday",
    "thursday", "friday", "saturday", "sunday", "tomorrow",
}

_GOODBYE_SIGNALS = {
    "bye", "goodbye", "thanks", "thank you", "that's all",
    "done", "no thanks", "never mind", "all good",
}


def _looks_like_confirmation(text: str) -> bool:
    """Cheap string check before spending tokens on APPOINTMENT_CONFIRM_SYSTEM."""
    lower = text.lower()
    return any(sig in lower for sig in _CONFIRM_SIGNALS)


# ══════════════════════════════════════════════════════════════════════════════
# CHAT GRAPH NODES
# ══════════════════════════════════════════════════════════════════════════════

def node_check_complete(state: dict) -> dict:
    """Mark conversation complete when all fields + appt booked, or on goodbye."""
    if state.get("is_complete"):
        return state  # already set — skip work

    has_all = all(not field_missing(state, f) for f in _REQUIRED)
    if has_all and state.get("appt_booked"):
        state["is_complete"] = True
        logger.info("complete: all fields + appt booked")
        return state

    msg = last_user_msg(state)
    if msg and any(sig in msg.lower() for sig in _GOODBYE_SIGNALS):
        state["is_complete"] = True
        logger.info(f"complete: goodbye signal in '{msg[:40]}'")

    return state


def node_chat_reply(state: dict) -> dict:
    """Generate AI reply. Injects slots + collected-fields context into system prompt."""
    try:
        if not state.get("appt_slots"):
            state["appt_slots"] = get_appt_slots()
        slots = state["appt_slots"]

        sys_msg = (
            HVAC_EXPERT_SYSTEM
            .replace("{slot_1}", slots[0])
            .replace("{slot_2}", slots[1])
            .replace("{slot_3}", slots[2])
        )

        all_fields  = _REQUIRED + ["urgency", "is_homeowner", "system_age"]
        collected   = {k: state.get(k) for k in all_fields}
        have        = {k: v for k, v in collected.items() if v is not None}
        missing_set = {k for k, v in collected.items() if v is None}

        # Pick the single next field to collect — follow priority order
        next_field = next(
            (f for f in _FIELD_PRIORITY if f in missing_set),
            "none",
        )

        guide = FIELD_COLLECTION_GUIDE.format(
            collected       = json.dumps(have, default=str),
            next_field      = next_field,
            collected_count = len(have),
            total_count     = len(all_fields),
        )

        messages = [SystemMessage(content=sys_msg + "\n" + guide)]
        messages += build_lc_messages(state)

        resp  = llm.invoke(messages, max_tokens=300, temperature=0.7)
        reply = resp.content.strip()

    except Exception as exc:
        logger.error(f"node_chat_reply failed: {exc}")
        reply = "Sorry, I had a brief technical issue. Could you repeat that?"

    state.setdefault("messages", []).append({
        "role": "assistant", "content": reply, "ts": datetime.utcnow().isoformat()
    })
    state["turn_count"] = state.get("turn_count", 0) + 1
    return state


def node_extract_fields(state: dict) -> dict:
    """
    Per-turn extraction from the latest user message.
    Appointment confirmation check only fires when:
      - Slots have been offered (state has appt_slots)
      - Appointment not yet booked
      - Message contains a confirmation-like keyword (pre-filter)
    """
    msg = last_user_msg(state)
    if not msg:
        return state

    # ── Field extraction ──────────────────────────────────────────────────────
    try:
        resp      = llm.invoke([
            SystemMessage(content=EXTRACT_FIELDS_SYSTEM),
            HumanMessage(content=msg),
        ], max_tokens=150, temperature=0)
        extracted = parse_json(resp.content)
        if extracted:
            merge_extracted(state, extracted)
    except Exception as exc:
        logger.error(f"node_extract_fields (fields) failed: {exc}")

    # ── Appointment confirmation — gated ──────────────────────────────────────
    if (
        state.get("appt_slots")
        and not state.get("appt_booked")
        and _looks_like_confirmation(msg)
    ):
        try:
            slots_str = "\n".join(f"{i+1}. {s}" for i, s in enumerate(state["appt_slots"]))
            resp = llm.invoke([
                SystemMessage(content=APPOINTMENT_CONFIRM_SYSTEM),
                HumanMessage(content=f"Slots offered:\n{slots_str}\n\nUser said: {msg}"),
            ], max_tokens=60, temperature=0)
            confirm = parse_json(resp.content)
            if confirm and confirm.get("confirmed"):
                idx = int(confirm.get("slot_index", 0))
                idx = max(0, min(idx, len(state["appt_slots"]) - 1))
                state["appt_booked"]    = True
                state["appt_confirmed"] = state["appt_slots"][idx]
                logger.info(f"appt booked: slot {idx} = {state['appt_confirmed']}")
        except Exception as exc:
            logger.error(f"node_extract_fields (appt) failed: {exc}")

    return state


# ══════════════════════════════════════════════════════════════════════════════
# POST-CHAT GRAPH NODES
# ══════════════════════════════════════════════════════════════════════════════

def node_extract_final(state: dict) -> dict:
    """
    Final extraction pass over full transcript.
    Skipped entirely if all required fields are already present —
    saves a full LLM call (~800 tokens) when chat extraction worked well.
    """
    missing = [f for f in _REQUIRED if field_missing(state, f)]
    if not missing:
        logger.info("node_extract_final: all required fields present — skipping")
        return state

    logger.info(f"node_extract_final: filling {missing}")
    try:
        transcript = full_transcript(state)
        if not transcript:
            return state
        resp      = llm.invoke([
            SystemMessage(content=EXTRACT_FIELDS_SYSTEM),
            HumanMessage(content=transcript),
        ], max_tokens=150, temperature=0)
        extracted = parse_json(resp.content)
        if extracted:
            merge_extracted(state, extracted)
    except Exception as exc:
        logger.error(f"node_extract_final failed: {exc}")

    return state


def node_score_lead(state: dict) -> dict:
    """
    Rule-based scoring — no LLM call.
    Consistent, debuggable, saves ~750 tokens per post-chat run.
    """
    result = rule_score_lead(state)
    state["score"]        = result["score"]
    state["score_number"] = result["score_number"]
    state["score_reason"] = result["score_reason"]
    logger.info(f"score: {result['score']} ({result['score_number']}) — {result['score_reason']}")
    return state


def node_generate_summary(state: dict) -> dict:
    """
    ONE LLM call produces both client + internal summaries.
    Previously two separate calls (~500 tokens overhead each time).
    """
    context = {
        "name":           state.get("name"),
        "issue":          state.get("issue"),
        "location":       state.get("location"),
        "system_age":     state.get("system_age"),
        "urgency":        state.get("urgency"),
        "is_homeowner":   state.get("is_homeowner"),
        "appt_confirmed": state.get("appt_confirmed"),
        "score":          state.get("score"),
        "score_reason":   state.get("score_reason"),
    }
    try:
        resp   = llm.invoke([
            SystemMessage(content=SUMMARY_COMBINED_SYSTEM),
            HumanMessage(content=json.dumps(context, default=str)),
        ], max_tokens=350, temperature=0.4)
        result = parse_json(resp.content)
        if result:
            state["summary"]          = result.get("client", "")
            state["internal_summary"] = result.get("internal", "")
        else:
            raise ValueError("No JSON in summary response")
    except Exception as exc:
        logger.error(f"node_generate_summary failed: {exc}")
        issue    = state.get("issue", "HVAC issue")
        location = state.get("location", "your area")
        appt     = state.get("appt_confirmed", "to be scheduled")
        score    = (state.get("score") or "warm").upper()
        state["summary"]          = (
            f"We discussed your {issue} in {location}. "
            f"Appointment: {appt}."
        )
        state["internal_summary"] = (
            f"{score} - {issue} | {state.get('score_reason', '')}"
        )

    return state


def node_send_email(state: dict) -> dict:
    """Send consultation summary email to client. Skips if no email collected."""
    if not state.get("email"):
        logger.info("node_send_email: no email — skipping")
        return state

    name    = state.get("name", "there")
    summary = state.get("summary", "Here is a summary of our conversation.")

    if state.get("appt_confirmed"):
        appt_html = f"""
        <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:8px;padding:16px;margin:16px 0;">
          <h3 style="margin:0 0 8px;color:#166534;">📅 Your Appointment</h3>
          <p style="margin:4px 0;font-size:16px;font-weight:600;">{state["appt_confirmed"]}</p>
          <p style="margin:4px 0;color:#555;">Free in-home assessment — tech calls 30 min before arrival.</p>
        </div>"""
    else:
        appt_html = f"""
        <div style="background:#fefce8;border:1px solid #fde047;border-radius:8px;padding:16px;margin:16px 0;">
          <p style="margin:0;">Reply to this email or call <strong>{settings.BUSINESS_PHONE}</strong> to book your free assessment.</p>
        </div>"""

    html = f"""<!DOCTYPE html><html><body style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px;color:#1a1a1a;">
      <h2 style="color:#0D1B2A;">Your HVAC Consultation Summary</h2>
      <p>Hi {name},</p><p>{summary}</p>
      {appt_html}
      <hr style="border:none;border-top:1px solid #e5e4e2;margin:24px 0;">
      <p style="color:#666;font-size:13px;">Questions? Reply or call <strong>{settings.BUSINESS_PHONE}</strong>.<br>automedge HVAC Team</p>
    </body></html>"""

    try:
        result = email_tool.send_email(
            to        = state["email"],
            subject   = "Your HVAC consultation + appointment",
            html      = html,
            from_name = "automedge HVAC",
        )
        state["email_sent"] = result.get("status") == "sent"
        logger.info(f"email sent={state['email_sent']} to {state['email']}")
    except Exception as exc:
        logger.error(f"node_send_email failed: {exc}")
        state["email_sent"] = False

    return state


def node_save_sheets(state: dict) -> dict:
    """Save lead row to the correct tab (Hot/Warm/Cold) in Google Sheets."""
    TAB = {"hot": "Hot Leads", "warm": "Warm Leads", "cold": "Cold Leads"}
    score = state.get("score", "warm")
    tab   = TAB.get(score, "Warm Leads")

    # Columns A–G — matches Sheet header row exactly
    row = [
        datetime.utcnow().isoformat(),       # A Timestamp
        state.get("name")         or "",     # B Name
        state.get("email")        or "",     # C Email
        state.get("phone")        or "",     # D Phone
        state.get("issue")        or "",     # E Issue
        state.get("location")     or "",     # F Address / Location
        state.get("vertical")     or "",     # G Vertical
        state.get("appt_confirmed") or "",   # H Appointment (blank if not booked)
    ]

    try:
        row_num = sheets_tool.save_lead_to_sheet(
            score=score, row=row, sheet_id=settings.HVAC_SHEET_ID
        )
        state["sheet_row"] = row_num
        state["sheet_tab"] = tab
        logger.info(f"sheets: tab='{tab}' row={row_num}")
    except Exception as exc:
        logger.error(f"node_save_sheets failed: {exc}")

    return state