# workflows/plumbing/nodes.py
# Plumbing-specific nodes.
# Key difference from HVAC/pest: emergency path skips diagnostic turns,
# jumps straight to address + phone collection and immediate dispatch.
import json
import logging
from datetime import datetime, timedelta

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from llm import llm
from core.config import settings
from workflows.plumbing.prompts import (
    PLUMBING_EXPERT_SYSTEM,
    FIELD_COLLECTION_GUIDE,
    EXTRACT_FIELDS_SYSTEM,
    APPOINTMENT_CONFIRM_SYSTEM,
    URGENCY_CLASSIFY_SYSTEM,
    LEAD_SCORING_SYSTEM,
    SUMMARY_CLIENT_SYSTEM,
    SUMMARY_INTERNAL_SYSTEM,
    SMS_EMERGENCY_DISPATCH,
)
from tools.email import email_tool
from tools.sheets import sheets_tool
from tools.sms import send_sms

logger = logging.getLogger(__name__)

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


def _is_emergency(state: dict) -> bool:
    """True if plumbing issue is an active emergency requiring immediate dispatch."""
    return (
        state.get("issue_type") == "emergency"
        or state.get("urgency") == "emergency"
        or state.get("has_water_damage") is True
    )


# ══════════════════════════════════════════════════════════════════════════════
# CHAT GRAPH NODES
# ══════════════════════════════════════════════════════════════════════════════

def node_check_complete(state: dict) -> dict:
    """
    Emergency path: complete when address + phone collected.
    Routine path: complete when all required fields + appt booked.
    """
    logger.info("node_check_complete [plumbing]")

    if _is_emergency(state):
        # Emergency only needs phone + location to dispatch
        has_emergency_info = (
            not _field_missing(state, "phone") and
            not _field_missing(state, "location")
        )
        if has_emergency_info:
            logger.info("Complete: emergency — phone + location collected")
            state["is_complete"] = True
            state["appt_booked"] = True   # emergency = immediate dispatch
            return state
    else:
        # Routine: need full info + appointment
        routine_required = ["name", "email", "phone", "issue", "location"]
        has_all = all(not _field_missing(state, f) for f in routine_required)
        if has_all and state.get("appt_booked"):
            logger.info("Complete: routine — all fields + appointment booked")
            state["is_complete"] = True
            return state

    last_user = _last_user_message(state)
    if last_user:
        end_signals = ["bye", "thanks", "goodbye", "done", "no thanks", "never mind"]
        if any(s in last_user.lower() for s in end_signals):
            logger.info("Complete: goodbye signal")
            state["is_complete"] = True

    return state


def node_chat_reply(state: dict) -> dict:
    """
    Generates Sam's reply.
    Emergency: terse, action-focused, skips diagnostic questions.
    Routine: thorough diagnostic conversation.
    """
    logger.info("node_chat_reply [plumbing]")
    try:
        if not state.get("appt_slots"):
            state["appt_slots"] = get_appointment_slots()

        slots = state["appt_slots"]
        issue_type = state.get("issue_type", "unknown")

        sys_msg = PLUMBING_EXPERT_SYSTEM
        sys_msg = sys_msg.replace("{slot_1}", slots[0])
        sys_msg = sys_msg.replace("{slot_2}", slots[1])
        sys_msg = sys_msg.replace("{slot_3}", slots[2])

        collected = {
            k: state.get(k)
            for k in [
                "name", "email", "phone", "location", "issue",
                "issue_type", "problem_area", "duration",
                "is_getting_worse", "has_water_damage",
                "main_shutoff_off", "is_homeowner", "property_type",
            ]
        }
        missing = [k for k, v in collected.items() if v is None]
        guide = FIELD_COLLECTION_GUIDE.format(
            current_state=json.dumps(collected, default=str),
            missing_fields=", ".join(missing) if missing else "none",
            issue_type=issue_type,
        )

        messages = [SystemMessage(content=sys_msg + "\n\n" + guide)]
        messages += _build_chat_messages(state)

        # Emergency: shorter, faster reply
        max_tokens = 150 if _is_emergency(state) else 300
        response   = llm.invoke(messages, max_tokens=max_tokens, temperature=0.6)
        reply      = response.content.strip()

        state.setdefault("messages", []).append({
            "role":    "assistant",
            "content": reply,
            "ts":      datetime.now().isoformat(),
        })
        state["turn_count"] = state.get("turn_count", 0) + 1

    except Exception as e:
        logger.error(f"node_chat_reply [plumbing] failed: {e}")
        state.setdefault("messages", []).append({
            "role":    "assistant",
            "content": "Sorry, I had a brief issue. Could you repeat that?",
            "ts":      datetime.now().isoformat(),
        })

    return state


def node_extract_fields(state: dict) -> dict:
    """
    Extracts plumbing-specific fields from latest user message.
    Emergency detection gates appointment confirmation logic.
    """
    logger.info("node_extract_fields [plumbing]")
    try:
        last_user = _last_user_message(state)
        if not last_user:
            return state

        response  = llm.invoke([
            SystemMessage(content=EXTRACT_FIELDS_SYSTEM),
            HumanMessage(content=last_user),
        ], max_tokens=300, temperature=0)

        extracted = _parse_json_from_llm(response.content)
        if extracted:
            state = _merge_extracted(state, extracted)

        # Appointment confirmation — routine only
        # Emergency path books immediately without slot selection
        if (
            not _is_emergency(state)
            and state.get("appt_slots")
            and not state.get("appt_booked")
        ):
            slots_str = "\n".join(
                f"{i+1}. {s}" for i, s in enumerate(state["appt_slots"])
            )
            confirm_response = llm.invoke([
                SystemMessage(content=APPOINTMENT_CONFIRM_SYSTEM),
                HumanMessage(
                    content=f"Available slots:\n{slots_str}\n\nUser message: {last_user}"
                ),
            ], max_tokens=80, temperature=0)

            confirm = _parse_json_from_llm(confirm_response.content)
            if confirm and confirm.get("confirmed"):
                idx = confirm.get("slot_index", 0)
                idx = idx if 0 <= idx < len(state["appt_slots"]) else 0
                state["appt_booked"]    = True
                state["appt_confirmed"] = state["appt_slots"][idx]
                logger.info(f"Appointment booked: {state['appt_confirmed']}")

    except Exception as e:
        logger.error(f"node_extract_fields [plumbing] failed: {e}")

    return state


# ══════════════════════════════════════════════════════════════════════════════
# POST-CHAT GRAPH NODES
# ══════════════════════════════════════════════════════════════════════════════

def node_extract_final(state: dict) -> dict:
    """Final extraction pass over full transcript."""
    logger.info("node_extract_final [plumbing]")
    try:
        transcript = _full_transcript(state)
        if not transcript:
            return state

        response  = llm.invoke([
            SystemMessage(content=EXTRACT_FIELDS_SYSTEM),
            HumanMessage(content=transcript),
        ], max_tokens=350, temperature=0)

        extracted = _parse_json_from_llm(response.content)
        if extracted:
            state = _merge_extracted(state, extracted)

    except Exception as e:
        logger.error(f"node_extract_final [plumbing] failed: {e}")

    return state


def node_score_urgency(state: dict) -> dict:
    """
    Classifies urgency as emergency/urgent/routine.
    Plumbing urgency is the most time-sensitive of all 4 verticals.
    Water damage compounds every minute — emergency must be detected fast.
    """
    logger.info("node_score_urgency [plumbing]")

    # Fast path: if already detected as emergency during chat, trust it
    if state.get("urgency") == "emergency" or state.get("issue_type") == "emergency":
        logger.info("Urgency already classified as emergency — skipping LLM call")
        state["urgency"] = "emergency"
        return state

    try:
        urgency_input = {
            "issue_type":      state.get("issue_type"),
            "issue":           state.get("issue"),
            "has_water_damage":state.get("has_water_damage"),
            "is_getting_worse":state.get("is_getting_worse"),
            "problem_area":    state.get("problem_area"),
            "property_type":   state.get("property_type"),
        }

        response = llm.invoke([
            SystemMessage(content=URGENCY_CLASSIFY_SYSTEM),
            HumanMessage(content=json.dumps(urgency_input)),
        ], max_tokens=100, temperature=0)

        result = _parse_json_from_llm(response.content)
        if result:
            urgency = result.get("urgency", "routine").lower()
            valid   = {"emergency", "urgent", "routine"}
            state["urgency"] = urgency if urgency in valid else "routine"
            logger.info(f"Urgency: {state['urgency']} | {result.get('reason')}")
        else:
            # Fallback: keyword-based detection
            issue = (state.get("issue") or "").lower()
            emergency_keywords = {
                "burst", "flooding", "flood", "spray", "sewage",
                "backup", "overflow", "gushing", "pouring",
            }
            urgent_keywords = {"no hot water", "no water", "overflow", "toilet overflow"}
            if any(kw in issue for kw in emergency_keywords):
                state["urgency"] = "emergency"
            elif any(kw in issue for kw in urgent_keywords):
                state["urgency"] = "urgent"
            else:
                state["urgency"] = "routine"

    except Exception as e:
        logger.error(f"node_score_urgency [plumbing] failed: {e}")
        state["urgency"] = "routine"

    return state


def node_emergency_sms(state: dict) -> dict:
    """
    Emergency-only node: sends immediate SMS dispatch confirmation.
    Only runs on emergency path in post_chat_graph.
    Routine leads get email confirmation only.
    """
    logger.info("node_emergency_sms [plumbing]")

    if not state.get("phone"):
        logger.info("No phone for emergency SMS — skipping")
        return state

    try:
        msg = SMS_EMERGENCY_DISPATCH.format(
            name=state.get("name", "there"),
            location=state.get("location", "your location"),
            business_phone=settings.BUSINESS_PHONE,
        )
        result = send_sms(to=state["phone"], body=msg)
        state["sms_sent"] = result.get("status") == "sent"
        logger.info(f"Emergency SMS sent={state['sms_sent']} to {state['phone']}")

    except Exception as e:
        logger.error(f"node_emergency_sms [plumbing] failed: {e}")
        state["sms_sent"] = False

    return state


def node_score_lead(state: dict) -> dict:
    """Scores lead hot/warm/cold with plumbing-specific criteria."""
    logger.info("node_score_lead [plumbing]")
    try:
        scoring_input = {
            "issue_type":      state.get("issue_type"),
            "urgency":         state.get("urgency"),
            "is_homeowner":    state.get("is_homeowner"),
            "has_water_damage":state.get("has_water_damage"),
            "is_getting_worse":state.get("is_getting_worse"),
            "property_type":   state.get("property_type"),
            "email":           bool(state.get("email")),
            "phone":           bool(state.get("phone")),
            "appt_booked":     state.get("appt_booked"),
            "turn_count":      state.get("turn_count"),
            "problem_area":    state.get("problem_area"),
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
            # Emergency always HOT even if parsing fails
            if state.get("urgency") == "emergency":
                state["score"]        = "hot"
                state["score_reason"] = "Emergency plumbing issue — auto-scored hot"
            else:
                state["score"]        = "warm"
                state["score_reason"] = "Could not parse scoring output"

    except Exception as e:
        logger.error(f"node_score_lead [plumbing] failed: {e}")
        state["score"]        = "hot" if _is_emergency(state) else "warm"
        state["score_reason"] = f"Scoring error: {str(e)}"

    return state


def node_generate_summary(state: dict) -> dict:
    """Two separate summaries: client email + internal Sheets note."""
    logger.info("node_generate_summary [plumbing]")

    context = {
        "name":            state.get("name"),
        "issue":           state.get("issue"),
        "issue_type":      state.get("issue_type"),
        "problem_area":    state.get("problem_area"),
        "location":        state.get("location"),
        "has_water_damage":state.get("has_water_damage"),
        "urgency":         state.get("urgency"),
        "is_homeowner":    state.get("is_homeowner"),
        "property_type":   state.get("property_type"),
        "appt_confirmed":  state.get("appt_confirmed"),
        "score":           state.get("score"),
        "score_reason":    state.get("score_reason"),
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
        logger.error(f"node_generate_summary (client) [plumbing] failed: {e}")
        appt = state.get("appt_confirmed", "to be scheduled")
        state["summary"] = (
            f"We discussed your {state.get('issue', 'plumbing issue')} "
            f"in {state.get('location', 'your area')}. "
            f"{'A plumber is being dispatched now.' if _is_emergency(state) else f'Appointment: {appt}.'}"
        )

    # Internal summary
    try:
        response = llm.invoke([
            SystemMessage(content=SUMMARY_INTERNAL_SYSTEM),
            HumanMessage(content=context_str),
        ], max_tokens=150, temperature=0.3)
        state["internal_summary"] = response.content.strip()
    except Exception as e:
        logger.error(f"node_generate_summary (internal) [plumbing] failed: {e}")
        state["internal_summary"] = (
            f"{'EMERGENCY' if _is_emergency(state) else state.get('urgency', 'routine').upper()} "
            f"{(state.get('score') or '').upper()} - "
            f"Issue: {state.get('issue')} | Reason: {state.get('score_reason')}"
        )

    return state


def node_send_email(state: dict) -> dict:
    """
    Sends confirmation email.
    Emergency: confirms dispatch + shutoff reminder.
    Routine: confirms appointment.
    """
    logger.info("node_send_email [plumbing]")

    if not state.get("email"):
        logger.info("No email — skipping")
        return state

    try:
        name       = state.get("name", "there")
        is_emerg   = _is_emergency(state)

        if is_emerg:
            action_section = f"""
            <div style="background:#fef2f2;border:1px solid #fca5a5;
                        border-radius:8px;padding:16px;margin:16px 0;">
                <h3 style="margin:0 0 8px;color:#991b1b;">
                    Emergency Dispatch Confirmed
                </h3>
                <p style="margin:4px 0;font-size:15px;font-weight:600;">
                    A plumber is on the way to {state.get("location", "your location")}.
                </p>
                <p style="margin:8px 0;color:#555;">
                    Keep your main water shutoff CLOSED until the plumber arrives.
                    You will receive a call within 15 minutes.
                </p>
                <p style="margin:4px 0;color:#555;">
                    Questions? Call <strong>{settings.BUSINESS_PHONE}</strong>
                </p>
            </div>
            """
        elif state.get("appt_confirmed"):
            action_section = f"""
            <div style="background:#f0fdf4;border:1px solid #86efac;
                        border-radius:8px;padding:16px;margin:16px 0;">
                <h3 style="margin:0 0 8px;color:#166534;">
                    Appointment Confirmed
                </h3>
                <p style="margin:4px 0;font-size:16px;font-weight:600;">
                    {state["appt_confirmed"]}
                </p>
                <p style="margin:4px 0;color:#555;">
                    Our plumber calls 20 minutes before arrival.
                    No work begins without your approval and a full quote.
                </p>
            </div>
            """
        else:
            action_section = f"""
            <div style="background:#fefce8;border:1px solid #fde047;
                        border-radius:8px;padding:16px;margin:16px 0;">
                <p style="margin:0;">
                    Reply to this email or call
                    <strong>{settings.BUSINESS_PHONE}</strong>
                    to schedule your visit.
                </p>
            </div>
            """

        subject = (
            "Emergency plumbing — plumber dispatched"
            if is_emerg
            else "Your plumbing appointment is confirmed"
        )

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family:sans-serif;max-width:600px;
                     margin:0 auto;padding:24px;color:#1a1a1a;">
            <h2 style="color:#0D1B2A;">
                {"Emergency Plumbing Response" if is_emerg else "Plumbing Appointment Summary"}
            </h2>
            <p>Hi {name},</p>
            <p>{state.get("summary", "Here is a summary of our consultation.")}</p>
            {action_section}
            <hr style="border:none;border-top:1px solid #e5e4e2;margin:24px 0;">
            <p style="color:#666;font-size:13px;">
                Questions? Call <strong>{settings.BUSINESS_PHONE}</strong>.<br>
                automedge Plumbing Team
            </p>
        </body>
        </html>
        """

        result = email_tool.send_email(
            to=state["email"],
            subject=subject,
            html=html_body,
            from_name="automedge Plumbing",
        )
        state["email_sent"] = result.get("status") == "sent"
        logger.info(f"Email sent={state['email_sent']} to {state['email']}")

    except Exception as e:
        logger.error(f"node_send_email [plumbing] failed: {e}")
        state["email_sent"] = False

    return state


def node_save_sheets(state: dict) -> dict:
    """Saves lead to correct Google Sheet tab."""
    logger.info("node_save_sheets [plumbing]")

    TAB_MAP = {"hot": "Hot Leads", "warm": "Warm Leads", "cold": "Cold Leads"}

    try:
        score = state.get("score", "warm")

        row = [
            datetime.now().isoformat(),                      # A Timestamp
            state.get("name") or "",                         # B Name
            state.get("email") or "",                        # C Email
            state.get("phone") or "",                        # D Phone
            state.get("location") or "",                     # E Location
            state.get("issue") or "",                        # F Issue
            state.get("issue_type") or "",                   # G Issue Type
            state.get("problem_area") or "",                 # H Problem Area
            state.get("duration") or "",                     # I Duration
            str(state.get("is_getting_worse") or ""),        # J Getting Worse
            str(state.get("has_water_damage") or ""),        # K Water Damage
            str(state.get("main_shutoff_off") or ""),        # L Shutoff Off
            state.get("property_type") or "",                # M Property Type
            str(state.get("is_homeowner") or ""),            # N Homeowner
            state.get("urgency") or "",                      # O Urgency
            score.upper(),                                   # P Score
            str(state.get("score_number") or ""),            # Q Score Number
            state.get("score_reason") or "",                 # R Score Reason
            str(state.get("appt_booked", False)),            # S Appt Booked
            state.get("appt_confirmed") or "",               # T Appt DateTime
            str(state.get("sms_sent", False)),               # U SMS Sent
            str(state.get("email_sent", False)),             # V Email Sent
            str(state.get("turn_count", 0)),                 # W Chat Turns
            state.get("internal_summary") or "",             # X Internal Summary
            state.get("session_id") or "",                   # Y Session ID
        ]

        row_num = sheets_tool.save_lead_to_sheet(
            score=score,
            row=row,
            sheet_id=settings.PLUMBING_SHEET_ID,
        )

        state["sheet_row"] = row_num
        state["sheet_tab"] = TAB_MAP.get(score, "Warm Leads")
        logger.info(f"Saved: tab={state['sheet_tab']} row={row_num}")

    except Exception as e:
        logger.error(f"node_save_sheets [plumbing] failed: {e}")

    return state