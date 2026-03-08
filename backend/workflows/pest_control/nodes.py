# workflows/pest_control/nodes.py
import json
import logging
from datetime import datetime, timedelta

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from llm import llm
from core.config import settings
from models.workflow import HVACChatState as PestChatState  # same shape, rename later
from workflows.pest_control.prompts import (
    PEST_EXPERT_SYSTEM,
    FIELD_COLLECTION_GUIDE,
    EXTRACT_FIELDS_SYSTEM,
    APPOINTMENT_CONFIRM_SYSTEM,
    URGENCY_CLASSIFY_SYSTEM,
    LEAD_SCORING_SYSTEM,
    SUMMARY_CLIENT_SYSTEM,
    SUMMARY_INTERNAL_SYSTEM,
)
from tools.email import email_tool
from tools.sheets import sheets_tool

logger = logging.getLogger(__name__)


# ── Helpers (same pattern as hvac/nodes.py) ───────────────────────────────────

_MISSING = object()

def _field_missing(state: dict, key: str) -> bool:
    val = state.get(key, _MISSING)
    return val is _MISSING or val is None


def _parse_json_from_llm(content: str) -> dict | None:
    start = content.find("{")
    end   = content.rfind("}") + 1
    if start == -1 or end == 0:
        return None
    try:
        return json.loads(content[start:end])
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse failed: {e} | raw: {content[start:end][:200]}")
        return None


def _merge_extracted(state: dict, extracted: dict) -> dict:
    """Merge non-null extracted fields. Never overwrite existing values."""
    for k, v in extracted.items():
        if v is None:
            continue
        if _field_missing(state, k):
            state[k] = v
            logger.debug(f"Extracted: {k} = {v}")
    return state


def _build_chat_messages(state: dict) -> list:
    result = []
    for m in state.get("messages", []):
        role    = m.get("role")
        content = m.get("content", "")
        if role == "user":
            result.append(HumanMessage(content=content))
        elif role == "assistant":
            result.append(AIMessage(content=content))
    return result


def _last_user_message(state: dict) -> str | None:
    messages = state.get("messages", [])
    return next(
        (m["content"] for m in reversed(messages) if m.get("role") == "user"),
        None,
    )


def _full_transcript(state: dict) -> str:
    return "\n".join(
        f"{m['role'].upper()}: {m['content']}"
        for m in state.get("messages", [])
    )


def get_appointment_slots() -> list[str]:
    today = datetime.now()
    return [
        (today + timedelta(days=1)).strftime("%A, %b %d at 10:00 AM"),
        (today + timedelta(days=2)).strftime("%A, %b %d at 2:00 PM"),
        (today + timedelta(days=3)).strftime("%A, %b %d at 9:00 AM"),
    ]


# ══════════════════════════════════════════════════════════════════════════════
# CHAT GRAPH NODES
# ══════════════════════════════════════════════════════════════════════════════

def node_check_complete(state: dict) -> dict:
    """
    Marks conversation complete when:
    1. All required fields collected AND appointment booked
    2. Last USER message contains a goodbye signal
    """
    logger.info("node_check_complete [pest]")

    required = ["name", "email", "phone", "issue", "location"]
    # pest_type replaces issue as primary field
    pest_required = ["name", "email", "phone", "pest_type", "location"]
    has_all = all(not _field_missing(state, f) for f in pest_required)

    if has_all and state.get("appt_booked"):
        logger.info("Complete: all pest fields + appointment booked")
        state["is_complete"] = True
        return state

    last_user = _last_user_message(state)
    if last_user:
        end_signals = ["bye", "thanks", "goodbye", "that's all", "done", "no thanks", "never mind"]
        if any(s in last_user.lower() for s in end_signals):
            logger.info("Complete: goodbye signal detected")
            state["is_complete"] = True

    return state


def node_chat_reply(state: dict) -> dict:
    """
    Generates Jordan's reply for this conversation turn.
    Pest-specific: tracks pest_type instead of HVAC issue.
    """
    logger.info("node_chat_reply [pest]")
    try:
        if not state.get("appt_slots"):
            state["appt_slots"] = get_appointment_slots()

        slots = state["appt_slots"]

        sys_msg = PEST_EXPERT_SYSTEM
        sys_msg = sys_msg.replace("{slot_1}", slots[0])
        sys_msg = sys_msg.replace("{slot_2}", slots[1])
        sys_msg = sys_msg.replace("{slot_3}", slots[2])

        # Pest-specific collected fields
        collected = {
            k: state.get(k)
            for k in [
                "name", "email", "phone", "location",
                "pest_type", "infestation_area", "duration",
                "has_damage", "tried_treatment", "is_homeowner",
                "wants_annual", "urgency", "property_type",
            ]
        }
        missing = [k for k, v in collected.items() if v is None]
        guide = FIELD_COLLECTION_GUIDE.format(
            current_state=json.dumps(collected, default=str),
            missing_fields=", ".join(missing) if missing else "none",
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
        logger.error(f"node_chat_reply [pest] failed: {e}")
        state.setdefault("messages", []).append({
            "role":    "assistant",
            "content": "Sorry, I had a brief issue. Could you repeat that?",
            "ts":      datetime.now().isoformat(),
        })

    return state


def node_extract_fields(state: dict) -> dict:
    """
    Extracts pest-specific fields from the latest user message.
    Also detects appointment confirmation.
    """
    logger.info("node_extract_fields [pest]")
    try:
        last_user = _last_user_message(state)
        if not last_user:
            return state

        # Field extraction
        response  = llm.invoke([
            SystemMessage(content=EXTRACT_FIELDS_SYSTEM),
            HumanMessage(content=last_user),
        ], max_tokens=250, temperature=0)

        extracted = _parse_json_from_llm(response.content)
        if extracted:
            # Map pest_type to issue field for base state compatibility
            if extracted.get("pest_type") and _field_missing(state, "pest_type"):
                state["pest_type"] = extracted["pest_type"]
                state["issue"]     = extracted["pest_type"]  # base state compat
            state = _merge_extracted(state, extracted)

        # Appointment confirmation
        if state.get("appt_slots") and not state.get("appt_booked"):
            slots_str = "\n".join(
                f"{i+1}. {s}" for i, s in enumerate(state["appt_slots"])
            )
            confirm_response = llm.invoke([
                SystemMessage(content=APPOINTMENT_CONFIRM_SYSTEM),
                HumanMessage(content=f"Available slots:\n{slots_str}\n\nUser message: {last_user}"),
            ], max_tokens=80, temperature=0)

            confirm = _parse_json_from_llm(confirm_response.content)
            if confirm and confirm.get("confirmed"):
                idx = confirm.get("slot_index", 0)
                idx = idx if 0 <= idx < len(state["appt_slots"]) else 0
                state["appt_booked"]    = True
                state["appt_confirmed"] = state["appt_slots"][idx]
                logger.info(f"Appointment booked: slot {idx} = {state['appt_confirmed']}")

    except Exception as e:
        logger.error(f"node_extract_fields [pest] failed: {e}")

    return state


# ══════════════════════════════════════════════════════════════════════════════
# POST-CHAT GRAPH NODES
# ══════════════════════════════════════════════════════════════════════════════

def node_extract_final(state: dict) -> dict:
    """Final extraction pass over full transcript. Fills any missed fields."""
    logger.info("node_extract_final [pest]")
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
            if extracted.get("pest_type") and _field_missing(state, "pest_type"):
                state["pest_type"] = extracted["pest_type"]
                state["issue"]     = extracted["pest_type"]
            state = _merge_extracted(state, extracted)

    except Exception as e:
        logger.error(f"node_extract_final [pest] failed: {e}")

    return state


def node_score_urgency(state: dict) -> dict:
    """
    Classifies urgency as high/medium/low using LLM.
    Used for graph routing — NOT lead scoring.
    Different from HVAC: pest urgency depends on species, not season.
    """
    logger.info("node_score_urgency [pest]")
    try:
        urgency_input = {
            "pest_type":     state.get("pest_type"),
            "has_damage":    state.get("has_damage"),
            "duration":      state.get("duration"),
            "property_type": state.get("property_type"),
            "tried_treatment": state.get("tried_treatment"),
        }

        response = llm.invoke([
            SystemMessage(content=URGENCY_CLASSIFY_SYSTEM),
            HumanMessage(content=json.dumps(urgency_input)),
        ], max_tokens=100, temperature=0)

        result = _parse_json_from_llm(response.content)
        if result:
            urgency = result.get("urgency", "medium").lower()
            state["urgency"] = urgency if urgency in ("high", "medium", "low") else "medium"
            logger.info(f"Urgency classified: {state['urgency']} | {result.get('reason')}")
        else:
            # Auto-derive from pest_type if LLM fails
            high_pests   = {"termites", "bed bugs", "rodents", "cockroaches", "wasps"}
            medium_pests = {"ants", "fleas", "mosquitoes"}
            pest         = (state.get("pest_type") or "").lower()
            if pest in high_pests or state.get("has_damage"):
                state["urgency"] = "high"
            elif pest in medium_pests:
                state["urgency"] = "medium"
            else:
                state["urgency"] = "low"

    except Exception as e:
        logger.error(f"node_score_urgency [pest] failed: {e}")
        state["urgency"] = "medium"

    return state


def node_score_lead(state: dict) -> dict:
    """Scores lead as hot/warm/cold with pest-specific criteria."""
    logger.info("node_score_lead [pest]")
    try:
        scoring_input = {
            "pest_type":      state.get("pest_type"),
            "urgency":        state.get("urgency"),
            "is_homeowner":   state.get("is_homeowner"),
            "has_damage":     state.get("has_damage"),
            "tried_treatment":state.get("tried_treatment"),
            "wants_annual":   state.get("wants_annual"),
            "email":          bool(state.get("email")),
            "phone":          bool(state.get("phone")),
            "appt_booked":    state.get("appt_booked"),
            "turn_count":     state.get("turn_count"),
            "property_type":  state.get("property_type"),
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
        logger.error(f"node_score_lead [pest] failed: {e}")
        state["score"]        = "warm"
        state["score_reason"] = f"Scoring error: {str(e)}"

    return state


def node_generate_summary(state: dict) -> dict:
    """
    Two separate LLM calls:
      state["summary"]          -> client email
      state["internal_summary"] -> Google Sheets
    """
    logger.info("node_generate_summary [pest]")

    context = {
        "name":           state.get("name"),
        "pest_type":      state.get("pest_type"),
        "infestation_area": state.get("infestation_area"),
        "location":       state.get("location"),
        "has_damage":     state.get("has_damage"),
        "urgency":        state.get("urgency"),
        "is_homeowner":   state.get("is_homeowner"),
        "wants_annual":   state.get("wants_annual"),
        "appt_confirmed": state.get("appt_confirmed"),
        "score":          state.get("score"),
        "score_reason":   state.get("score_reason"),
    }
    context_str = json.dumps(context, default=str)

    # Client summary
    try:
        response = llm.invoke([
            SystemMessage(content=SUMMARY_CLIENT_SYSTEM),
            HumanMessage(content=context_str),
        ], max_tokens=250, temperature=0.5)
        state["summary"] = response.content.strip()
    except Exception as e:
        logger.error(f"node_generate_summary (client) [pest] failed: {e}")
        state["summary"] = (
            f"We discussed your {state.get('pest_type', 'pest')} issue "
            f"in {state.get('location', 'your area')}. "
            f"Appointment: {state.get('appt_confirmed', 'to be scheduled')}."
        )

    # Internal summary
    try:
        response = llm.invoke([
            SystemMessage(content=SUMMARY_INTERNAL_SYSTEM),
            HumanMessage(content=context_str),
        ], max_tokens=150, temperature=0.3)
        state["internal_summary"] = response.content.strip()
    except Exception as e:
        logger.error(f"node_generate_summary (internal) [pest] failed: {e}")
        state["internal_summary"] = (
            f"Score: {state.get('score', 'warm')} | "
            f"Pest: {state.get('pest_type')} | "
            f"Reason: {state.get('score_reason')}"
        )

    return state


def node_send_email(state: dict) -> dict:
    """Sends inspection confirmation + summary to client via Resend."""
    logger.info("node_send_email [pest]")

    if not state.get("email"):
        logger.info("No email — skipping")
        return state

    try:
        name = state.get("name", "there")

        if state.get("appt_confirmed"):
            appt_section = f"""
            <div style="background:#f0fdf4;border:1px solid #86efac;
                        border-radius:8px;padding:16px;margin:16px 0;">
                <h3 style="margin:0 0 8px;color:#166534;">
                    Inspection Confirmed
                </h3>
                <p style="margin:4px 0;font-size:16px;font-weight:600;">
                    {state["appt_confirmed"]}
                </p>
                <p style="margin:4px 0;color:#555;">Free pest inspection</p>
                <p style="margin:4px 0;color:#555;">
                    Specialist calls 15 minutes before arrival.
                </p>
            </div>
            """
        else:
            appt_section = f"""
            <div style="background:#fefce8;border:1px solid #fde047;
                        border-radius:8px;padding:16px;margin:16px 0;">
                <p style="margin:0;">
                    We would love to get you scheduled. Reply to this email
                    or call <strong>{settings.BUSINESS_PHONE}</strong>.
                </p>
            </div>
            """

        # Annual plan section — only if interest expressed
        annual_section = ""
        if state.get("wants_annual"):
            annual_section = """
            <div style="background:#eff6ff;border:1px solid #93c5fd;
                        border-radius:8px;padding:16px;margin:16px 0;">
                <h3 style="margin:0 0 8px;color:#1e40af;">
                    Annual Protection Plan
                </h3>
                <p style="margin:0;color:#555;">
                    Our specialist will walk you through annual protection
                    plan options during the inspection — quarterly treatments
                    and free re-treatments included.
                </p>
            </div>
            """

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family:sans-serif;max-width:600px;
                     margin:0 auto;padding:24px;color:#1a1a1a;">

            <h2 style="color:#0D1B2A;">Your Pest Control Inspection Summary</h2>
            <p>Hi {name},</p>
            <p>{state.get("summary", "Here is a summary of our consultation.")}</p>

            {appt_section}
            {annual_section}

            <hr style="border:none;border-top:1px solid #e5e4e2;margin:24px 0;">
            <p style="color:#666;font-size:13px;">
                Questions? Reply to this email or call
                <strong>{settings.BUSINESS_PHONE}</strong>.<br>
                automedge Pest Control Team
            </p>

        </body>
        </html>
        """

        result = email_tool.send_email(
            to=state["email"],
            subject="Your pest inspection summary + appointment",
            html=html_body,
            from_name="automedge Pest Control",
        )
        state["email_sent"] = result.get("status") == "sent"
        logger.info(f"Email sent={state['email_sent']} to {state['email']}")

    except Exception as e:
        logger.error(f"node_send_email [pest] failed: {e}")
        state["email_sent"] = False

    return state


def node_save_sheets(state: dict) -> dict:
    """
    Saves to correct Google Sheet tab.
    Pest-specific columns include: pest_type, infestation_area,
    has_damage, tried_treatment, wants_annual, property_type.
    """
    logger.info("node_save_sheets [pest]")

    TAB_MAP = {
        "hot":  "Hot Leads",
        "warm": "Warm Leads",
        "cold": "Cold Leads",
    }

    try:
        score = state.get("score", "warm")

        # Columns A-U (pest control has more fields than HVAC)
        row = [
            datetime.now().isoformat(),                      # A Timestamp
            state.get("name") or "",                         # B Name
            state.get("email") or "",                        # C Email
            state.get("phone") or "",                        # D Phone
            state.get("location") or "",                     # E Location
            state.get("pest_type") or "",                    # F Pest Type
            state.get("infestation_area") or "",             # G Infestation Area
            state.get("duration") or "",                     # H Duration
            str(state.get("has_damage") or ""),              # I Has Damage
            str(state.get("tried_treatment") or ""),         # J Tried Treatment
            state.get("property_type") or "",                # K Property Type
            str(state.get("is_homeowner") or ""),            # L Homeowner
            str(state.get("wants_annual") or ""),            # M Wants Annual Plan
            state.get("urgency") or "",                      # N Urgency
            score.upper(),                                   # O Score
            str(state.get("score_number") or ""),            # P Score Number
            state.get("score_reason") or "",                 # Q Score Reason
            str(state.get("appt_booked", False)),            # R Appt Booked
            state.get("appt_confirmed") or "",               # S Appt DateTime
            str(state.get("email_sent", False)),             # T Email Sent
            str(state.get("turn_count", 0)),                 # U Chat Turns
            state.get("internal_summary") or "",             # V Internal Summary
            state.get("session_id") or "",                   # W Session ID
        ]

        row_num = sheets_tool.save_lead_to_sheet(
            score=score,
            row=row,
            sheet_id=settings.PEST_SHEET_ID,
        )

        state["sheet_row"] = row_num
        state["sheet_tab"] = TAB_MAP.get(score, "Warm Leads")
        logger.info(f"Saved: tab={state['sheet_tab']} row={row_num}")

    except Exception as e:
        logger.error(f"node_save_sheets [pest] failed: {e}")

    return state