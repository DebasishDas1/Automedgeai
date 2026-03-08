import json
import logging
from datetime import datetime, timedelta
from typing import Any

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from llm import llm
from core.config import settings
from models.workflow import HVACChatState
from workflows.hvac.prompts import (
    HVAC_EXPERT_SYSTEM,
    FIELD_COLLECTION_GUIDE,
    EXTRACT_FIELDS_SYSTEM,
    LEAD_SCORING_SYSTEM,
    APPOINTMENT_CONFIRM_SYSTEM,
    SUMMARY_CLIENT_SYSTEM,
    SUMMARY_INTERNAL_SYSTEM,
)
from tools.email import email_tool
from tools.sheets import sheets_tool

logger = logging.getLogger(__name__)

# ── Sentinel for "field not yet collected" ────────────────────────────────────
# Needed because `not state.get(k)` fails when value is False (e.g. is_homeowner=False)
_MISSING = object()

def _field_missing(state: HVACChatState, key: str) -> bool:
    """Returns True only if field has never been set. False is a valid value."""
    val = state.get(key, _MISSING)
    return val is _MISSING or val is None


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_appointment_slots() -> list[str]:
    today = datetime.now()
    return [
        (today + timedelta(days=1)).strftime("%A, %b %d at 10:00 AM"),
        (today + timedelta(days=2)).strftime("%A, %b %d at 2:00 PM"),
        (today + timedelta(days=3)).strftime("%A, %b %d at 9:00 AM"),
    ]


def _parse_json_from_llm(content: str) -> dict | None:
    """Safely extract the first JSON object from an LLM response string."""
    start = content.find("{")
    end   = content.rfind("}") + 1
    if start == -1 or end == 0:
        return None
    try:
        return json.loads(content[start:end])
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse failed: {e} | raw: {content[start:end][:200]}")
        return None


def _merge_extracted(state: HVACChatState, extracted: dict) -> HVACChatState:
    """
    Merge extracted fields into state.
    Rules:
      - Never overwrite an existing non-None value (first capture wins)
      - Exception: is_homeowner — bool False is a valid value, use _field_missing
    """
    for k, v in extracted.items():
        if v is None:
            continue
        if _field_missing(state, k):
            state[k] = v
            logger.debug(f"Extracted field: {k} = {v}")
    return state


def _build_chat_messages(state: HVACChatState) -> list:
    """Convert state messages list to LangChain message objects."""
    result = []
    for m in state.get("messages", []):
        role    = m.get("role")
        content = m.get("content", "")
        if role == "user":
            result.append(HumanMessage(content=content))
        elif role == "assistant":
            result.append(AIMessage(content=content))
    return result


def _last_user_message(state: HVACChatState) -> str | None:
    """Returns the content of the most recent user message."""
    messages = state.get("messages", [])
    return next(
        (m["content"] for m in reversed(messages) if m.get("role") == "user"),
        None
    )


def _full_transcript(state: HVACChatState) -> str:
    """Returns full conversation as plain text for extraction/summary."""
    return "\n".join(
        f"{m['role'].upper()}: {m['content']}"
        for m in state.get("messages", [])
    )


# ══════════════════════════════════════════════════════════════════════════════
# CHAT GRAPH NODES
# ══════════════════════════════════════════════════════════════════════════════

def node_check_complete(state: HVACChatState) -> HVACChatState:
    """
    Decides if the conversation is done.
    Checks:
      1. All required fields collected + appointment booked
      2. Last USER message (not AI) contains a goodbye signal
    """
    logger.info("node_check_complete")

    required = ["name", "email", "phone", "issue", "location"]
    has_all  = all(not _field_missing(state, f) for f in required)

    if has_all and state.get("appt_booked"):
        logger.info("Complete: all fields + appointment booked")
        state["is_complete"] = True
        return state

    # Check last USER message — not last message (could be AI)
    last_user = _last_user_message(state)
    if last_user:
        end_signals = ["bye", "thanks", "goodbye", "that's all", "done", "no thanks", "never mind"]
        if any(signal in last_user.lower() for signal in end_signals):
            logger.info(f"Complete: goodbye signal detected in: '{last_user[:50]}'")
            state["is_complete"] = True

    return state


def node_chat_reply(state: HVACChatState) -> HVACChatState:
    """
    Generates the AI HVAC expert reply for this turn.
    Injects available slots and collected fields as context.
    """
    logger.info("node_chat_reply")
    try:
        # Generate slots once per session
        if not state.get("appt_slots"):
            state["appt_slots"] = get_appointment_slots()

        slots = state["appt_slots"]

        # Inject real dates into system prompt
        sys_msg = HVAC_EXPERT_SYSTEM.replace("{slot_1}", slots[0])
        sys_msg = sys_msg.replace("{slot_2}", slots[1])
        sys_msg = sys_msg.replace("{slot_3}", slots[2])

        # Build field collection guide
        collected = {
            k: state.get(k)
            for k in ["name", "email", "phone", "location", "issue",
                      "urgency", "is_homeowner", "system_age"]
        }
        missing = [k for k, v in collected.items() if v is None]
        guide = FIELD_COLLECTION_GUIDE.format(
            current_state=json.dumps(collected, default=str),
            missing_fields=", ".join(missing) if missing else "none — ready to book",
        )

        messages = [SystemMessage(content=sys_msg + "\n\n" + guide)]
        messages += _build_chat_messages(state)

        response = llm.invoke(messages, max_tokens=300, temperature=0.7)
        reply    = response.content.strip()

        state.setdefault("messages", []).append({
            "role":    "assistant",
            "content": reply,
            "ts":      datetime.now().isoformat(),
        })
        state["turn_count"] = state.get("turn_count", 0) + 1

    except Exception as e:
        logger.error(f"node_chat_reply failed: {e}")
        # Fallback reply — never leave user with no response
        state.setdefault("messages", []).append({
            "role":    "assistant",
            "content": "Sorry, I'm having a brief technical issue. Could you repeat that?",
            "ts":      datetime.now().isoformat(),
        })

    return state


def node_extract_fields(state: HVACChatState) -> HVACChatState:
    """
    Extracts structured fields from the latest user message.
    Also detects appointment confirmation using a dedicated LLM call.
    """
    logger.info("node_extract_fields")
    try:
        last_user = _last_user_message(state)
        if not last_user:
            return state

        # ── Field extraction ──────────────────────────────────────────────────
        response  = llm.invoke([
            SystemMessage(content=EXTRACT_FIELDS_SYSTEM),
            HumanMessage(content=last_user),
        ], max_tokens=200, temperature=0)

        extracted = _parse_json_from_llm(response.content)
        if extracted:
            state = _merge_extracted(state, extracted)

        # ── Appointment confirmation ──────────────────────────────────────────
        # Only check if slots were offered and not yet booked
        if state.get("appt_slots") and not state.get("appt_booked"):
            slots_str = "\n".join(
                f"{i+1}. {s}" for i, s in enumerate(state["appt_slots"])
            )
            confirm_response = llm.invoke([
                SystemMessage(content=APPOINTMENT_CONFIRM_SYSTEM),
                HumanMessage(content=(
                    f"Available slots:\n{slots_str}\n\n"
                    f"User message: {last_user}"
                )),
            ], max_tokens=100, temperature=0)

            confirm = _parse_json_from_llm(confirm_response.content)
            if confirm and confirm.get("confirmed"):
                slot_index = confirm.get("slot_index", 0)
                # Validate index is in range
                if 0 <= slot_index < len(state["appt_slots"]):
                    state["appt_booked"]    = True
                    state["appt_confirmed"] = state["appt_slots"][slot_index]
                    logger.info(f"Appointment booked: slot {slot_index} = {state['appt_confirmed']}")
                else:
                    # Fallback: use first slot if index is invalid
                    state["appt_booked"]    = True
                    state["appt_confirmed"] = state["appt_slots"][0]
                    logger.warning(f"Slot index {slot_index} out of range, defaulting to slot 0")

    except Exception as e:
        logger.error(f"node_extract_fields failed: {e}")

    return state


# ══════════════════════════════════════════════════════════════════════════════
# POST-CHAT GRAPH NODES
# ══════════════════════════════════════════════════════════════════════════════

def node_extract_final(state: HVACChatState) -> HVACChatState:
    """
    Final extraction pass over the FULL transcript.
    Fills any fields missed during per-turn extraction.
    """
    logger.info("node_extract_final")
    try:
        transcript = _full_transcript(state)
        if not transcript:
            return state

        response  = llm.invoke([
            SystemMessage(content=EXTRACT_FIELDS_SYSTEM),
            HumanMessage(content=transcript),
        ], max_tokens=300, temperature=0)

        extracted = _parse_json_from_llm(response.content)
        if extracted:
            state = _merge_extracted(state, extracted)

    except Exception as e:
        logger.error(f"node_extract_final failed: {e}")

    return state


def node_score_lead(state: HVACChatState) -> HVACChatState:
    """
    Scores lead as hot / warm / cold using LLM.
    Defaults to 'warm' on any failure.
    """
    logger.info("node_score_lead")
    try:
        # Only send scoring-relevant fields — not full messages array
        scoring_input = {
            "urgency":       state.get("urgency"),
            "is_homeowner":  state.get("is_homeowner"),
            "email":         bool(state.get("email")),
            "phone":         bool(state.get("phone")),
            "appt_booked":   state.get("appt_booked"),
            "turn_count":    state.get("turn_count"),
            "issue":         state.get("issue"),
            "budget_signal": state.get("budget_signal"),
            "timeline":      state.get("timeline"),
        }

        response = llm.invoke([
            SystemMessage(content=LEAD_SCORING_SYSTEM),
            HumanMessage(content=json.dumps(scoring_input)),
        ], max_tokens=150, temperature=0)

        result = _parse_json_from_llm(response.content)
        if result:
            score = result.get("score", "warm").lower()
            state["score"]        = score if score in ("hot", "warm", "cold") else "warm"
            state["score_reason"] = result.get("reason", "")
            logger.info(f"Lead scored: {state['score']} | {state['score_reason']}")
        else:
            state["score"]        = "warm"
            state["score_reason"] = "Could not parse scoring output"

    except Exception as e:
        logger.error(f"node_score_lead failed: {e}")
        state["score"]        = "warm"
        state["score_reason"] = f"Scoring error: {str(e)}"

    return state


def node_generate_summary(state: HVACChatState) -> HVACChatState:
    """
    Generates TWO separate summaries:
      state["summary"]          → client-facing, sent in email
      state["internal_summary"] → sales team, stored in Sheets
    Only sends relevant fields to LLM — never the full messages array.
    """
    logger.info("node_generate_summary")

    # Structured context — no message history, no extra tokens
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
        "budget_signal":  state.get("budget_signal"),
    }
    context_str = json.dumps(context, default=str)

    # ── Client summary ────────────────────────────────────────────────────────
    try:
        response = llm.invoke([
            SystemMessage(content=SUMMARY_CLIENT_SYSTEM),
            HumanMessage(content=context_str),
        ], max_tokens=300, temperature=0.5)
        state["summary"] = response.content.strip()
    except Exception as e:
        logger.error(f"node_generate_summary (client) failed: {e}")
        state["summary"] = (
            f"We discussed your {state.get('issue', 'HVAC issue')} "
            f"in {state.get('location', 'your area')}. "
            f"Appointment: {state.get('appt_confirmed', 'to be scheduled')}."
        )

    # ── Internal summary ──────────────────────────────────────────────────────
    try:
        response = llm.invoke([
            SystemMessage(content=SUMMARY_INTERNAL_SYSTEM),
            HumanMessage(content=context_str),
        ], max_tokens=200, temperature=0.3)
        state["internal_summary"] = response.content.strip()
    except Exception as e:
        logger.error(f"node_generate_summary (internal) failed: {e}")
        state["internal_summary"] = (
            f"Score: {state.get('score', 'warm')} | "
            f"Issue: {state.get('issue')} | "
            f"Reason: {state.get('score_reason')}"
        )

    return state


def node_send_email(state: HVACChatState) -> HVACChatState:
    """
    Sends consultation summary email to client via Resend.
    Skips silently if no email was collected.
    Business phone comes from settings — never hardcoded.
    """
    logger.info("node_send_email")

    if not state.get("email"):
        logger.info("No email collected — skipping email send")
        return state

    try:
        name    = state.get("name", "there")
        summary = state.get("summary", "Here is a summary of our conversation.")

        # ── Appointment section ───────────────────────────────────────────────
        if state.get("appt_confirmed"):
            appt_section = f"""
            <div style="background:#f0fdf4;border:1px solid #86efac;
                        border-radius:8px;padding:16px;margin:16px 0;">
                <h3 style="margin:0 0 8px;color:#166534;">📅 Your Appointment</h3>
                <p style="margin:4px 0;font-size:16px;font-weight:600;">
                    {state['appt_confirmed']}
                </p>
                <p style="margin:4px 0;color:#555;">Free in-home assessment</p>
                <p style="margin:4px 0;color:#555;">
                    Our technician will call 30 minutes before arrival.
                </p>
            </div>
            """
        else:
            appt_section = f"""
            <div style="background:#fefce8;border:1px solid #fde047;
                        border-radius:8px;padding:16px;margin:16px 0;">
                <p style="margin:0;">
                    We'd love to get you scheduled. Reply to this email
                    or call us at
                    <strong>{settings.BUSINESS_PHONE}</strong>
                    to book your free assessment.
                </p>
            </div>
            """

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family:sans-serif;max-width:600px;
                     margin:0 auto;padding:24px;color:#1a1a1a;">

            <h2 style="color:#0D1B2A;">Your HVAC Consultation Summary</h2>
            <p>Hi {name},</p>
            <p>{summary}</p>

            {appt_section}

            <hr style="border:none;border-top:1px solid #e5e4e2;margin:24px 0;">
            <p style="color:#666;font-size:13px;">
                Questions? Reply to this email or call
                <strong>{settings.BUSINESS_PHONE}</strong>.<br>
                automedge HVAC Team
            </p>

        </body>
        </html>
        """

        result = email_tool.send_email(
            to=state["email"],
            subject="Your HVAC consultation summary + appointment",
            html=html_body,
            from_name="automedge HVAC",
        )
        state["email_sent"] = result.get("status") == "sent"
        logger.info(f"Email sent={state['email_sent']} to {state['email']}")

    except Exception as e:
        logger.error(f"node_send_email failed: {e}")
        state["email_sent"] = False

    return state


def node_save_sheets(state: HVACChatState) -> HVACChatState:
    """
    Saves lead to the correct Google Sheet tab based on score.
    hot → "Hot Leads" | warm → "Warm Leads" | cold → "Cold Leads"
    Stores row number for future updates (stage changes, etc.)
    """
    logger.info("node_save_sheets")

    TAB_MAP = {
        "hot":  "Hot Leads",
        "warm": "Warm Leads",
        "cold": "Cold Leads",
    }

    try:
        score   = state.get("score", "warm")
        tab     = TAB_MAP.get(score, "Warm Leads")

        # Columns A–S (matches Sheet header row exactly)
        row = [
            datetime.now().isoformat(),                    # A Timestamp
            state.get("name") or "",                       # B Name
            state.get("email") or "",                      # C Email
            state.get("phone") or "",                      # D Phone
            state.get("location") or "",                   # E Location
            state.get("issue") or "",                      # F Issue
            state.get("system_age") or "",                 # G System Age
            state.get("urgency") or "",                    # H Urgency
            str(state.get("is_homeowner") or ""),          # I Homeowner
            state.get("budget_signal") or "",              # J Budget Signal
            score.upper(),                                 # K Score
            str(state.get("score_number") or ""),          # L Score Number
            state.get("score_reason") or "",               # M Score Reason
            str(state.get("appt_booked", False)),          # N Appt Booked
            state.get("appt_confirmed") or "",             # O Appt DateTime
            str(state.get("email_sent", False)),           # P Email Sent
            str(state.get("turn_count", 0)),               # Q Chat Turns
            state.get("internal_summary") or "",           # R Internal Summary
            state.get("session_id") or "",                 # S Session ID
        ]

        row_num = sheets_tool.save_lead_to_sheet(
            score=score,
            row=row,
            sheet_id=settings.HVAC_SHEET_ID,
        )

        state["sheet_row"] = row_num
        state["sheet_tab"] = tab
        logger.info(f"Saved to sheet tab='{tab}' row={row_num}")

    except Exception as e:
        logger.error(f"node_save_sheets failed: {e}")

    return state