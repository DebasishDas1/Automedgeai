# workflows/roofing/nodes.py
# Roofing-specific nodes.
# Key difference from all other verticals:
#   storm + insurance path changes scoring, email content, and SMS templates.
#   Commercial properties are auto-priority (multiple units = multiple jobs).
#   Urgency = storm_damage|leak_active|inspection_needed|planning (not high/medium/low).
import json
import logging
from datetime import datetime, timedelta

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from llm import llm
from core.config import settings
from workflows.roofing.prompts import (
    ROOFING_EXPERT_SYSTEM,
    FIELD_COLLECTION_GUIDE,
    EXTRACT_FIELDS_SYSTEM,
    APPOINTMENT_CONFIRM_SYSTEM,
    URGENCY_CLASSIFY_SYSTEM,
    LEAD_SCORING_SYSTEM,
    SUMMARY_CLIENT_SYSTEM,
    SUMMARY_INTERNAL_SYSTEM,
    SMS_INSPECTION_CONFIRM,
    SMS_INSURANCE_REMINDER,
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
    return next(
        (m["content"] for m in reversed(state.get("messages", [])) if m.get("role") == "user"),
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


def _is_storm_insurance_lead(state: dict) -> bool:
    """True if this is the highest-value lead type: storm damage + insurance."""
    return (
        state.get("damage_type") == "storm"
        and state.get("has_insurance") is True
    )


def _is_commercial(state: dict) -> bool:
    return state.get("property_type") == "commercial"


# ══════════════════════════════════════════════════════════════════════════════
# CHAT GRAPH NODES
# ══════════════════════════════════════════════════════════════════════════════

def node_check_complete(state: dict) -> dict:
    """
    Complete when all required fields collected + appointment booked.
    Roofing has no emergency dispatch — inspection is always the next step.
    """
    logger.info("node_check_complete [roofing]")

    required = ["name", "email", "phone", "damage_type", "location"]
    has_all  = all(not _field_missing(state, f) for f in required)

    if has_all and state.get("appt_booked"):
        logger.info("Complete: all roofing fields + inspection booked")
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
    Generates Jordan's reply.
    Storm path: introduces insurance assistance after slot confirmation.
    Commercial: prioritizes scope and multiple-unit details.
    """
    logger.info("node_chat_reply [roofing]")
    try:
        if not state.get("appt_slots"):
            state["appt_slots"] = get_appointment_slots()

        slots       = state["appt_slots"]
        damage_type = state.get("damage_type", "unknown")

        sys_msg = ROOFING_EXPERT_SYSTEM
        sys_msg = sys_msg.replace("{slot_1}", slots[0])
        sys_msg = sys_msg.replace("{slot_2}", slots[1])
        sys_msg = sys_msg.replace("{slot_3}", slots[2])

        collected = {
            k: state.get(k)
            for k in [
                "name", "email", "phone", "location",
                "damage_type", "damage_detail", "storm_date",
                "roof_age", "has_insurance", "insurance_contacted",
                "adjuster_involved", "has_interior_leak",
                "is_homeowner", "property_type",
            ]
        }
        missing = [k for k, v in collected.items() if v is None]
        guide = FIELD_COLLECTION_GUIDE.format(
            current_state=json.dumps(collected, default=str),
            missing_fields=", ".join(missing) if missing else "none",
            damage_type=damage_type,
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
        logger.error(f"node_chat_reply [roofing] failed: {e}")
        state.setdefault("messages", []).append({
            "role":    "assistant",
            "content": "Sorry, I had a brief issue. Could you repeat that?",
            "ts":      datetime.now().isoformat(),
        })

    return state


def node_extract_fields(state: dict) -> dict:
    """
    Extracts roofing-specific fields from latest user message.
    Tracks insurance signals as first-class fields.
    """
    logger.info("node_extract_fields [roofing]")
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

        # Appointment confirmation
        if state.get("appt_slots") and not state.get("appt_booked"):
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
                logger.info(f"Inspection booked: {state['appt_confirmed']}")

    except Exception as e:
        logger.error(f"node_extract_fields [roofing] failed: {e}")

    return state


# ══════════════════════════════════════════════════════════════════════════════
# POST-CHAT GRAPH NODES
# ══════════════════════════════════════════════════════════════════════════════

def node_extract_final(state: dict) -> dict:
    """Final extraction pass over full transcript."""
    logger.info("node_extract_final [roofing]")
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
        logger.error(f"node_extract_final [roofing] failed: {e}")

    return state


def node_score_urgency(state: dict) -> dict:
    """
    Classifies roofing urgency as storm_damage|leak_active|inspection_needed|planning.
    Storm claims have insurance filing deadlines — time-critical even without active damage.
    """
    logger.info("node_score_urgency [roofing]")

    # Fast path: storm already confirmed during chat
    if state.get("damage_type") == "storm" and state.get("urgency") == "storm_damage":
        logger.info("Urgency already classified as storm_damage — skipping LLM")
        return state

    try:
        urgency_input = {
            "damage_type":         state.get("damage_type"),
            "storm_date":          state.get("storm_date"),
            "has_interior_leak":   state.get("has_interior_leak"),
            "insurance_contacted": state.get("insurance_contacted"),
            "adjuster_involved":   state.get("adjuster_involved"),
            "roof_age":            state.get("roof_age"),
            "urgency":             state.get("urgency"),
        }

        response = llm.invoke([
            SystemMessage(content=URGENCY_CLASSIFY_SYSTEM),
            HumanMessage(content=json.dumps(urgency_input)),
        ], max_tokens=100, temperature=0)

        result = _parse_json_from_llm(response.content)
        if result:
            urgency = result.get("urgency", "inspection_needed").lower()
            valid   = {"storm_damage", "leak_active", "inspection_needed", "planning"}
            state["urgency"] = urgency if urgency in valid else "inspection_needed"
            logger.info(f"Urgency: {state['urgency']} | {result.get('reason')}")
        else:
            # Keyword fallback
            damage = (state.get("damage_type") or "").lower()
            state["urgency"] = "storm_damage" if damage == "storm" else "inspection_needed"

    except Exception as e:
        logger.error(f"node_score_urgency [roofing] failed: {e}")
        state["urgency"] = "inspection_needed"

    return state


def node_insurance_sms(state: dict) -> dict:
    """
    Storm + insurance path only.
    Sends a pre-inspection SMS reminding them to have policy info ready.
    This is a touchpoint unique to roofing — no other vertical has it.
    Helps with show rate (homeowner is prepared, feels more committed).
    """
    logger.info("node_insurance_sms [roofing]")

    if not state.get("phone"):
        logger.info("No phone for insurance SMS — skipping")
        return state

    if not _is_storm_insurance_lead(state):
        logger.info("Not a storm+insurance lead — skipping insurance SMS")
        return state

    try:
        msg = SMS_INSURANCE_REMINDER.format(
            name=state.get("name", "there"),
            appt_datetime=state.get("appt_confirmed", "your upcoming inspection"),
            business_phone=settings.BUSINESS_PHONE,
        )
        result = send_sms(to=state["phone"], body=msg)
        state["sms_sent"] = result.get("status") == "sent"
        logger.info(f"Insurance reminder SMS sent={state['sms_sent']} to {state['phone']}")

    except Exception as e:
        logger.error(f"node_insurance_sms [roofing] failed: {e}")
        state["sms_sent"] = False

    return state


def node_score_lead(state: dict) -> dict:
    """
    Scores roofing lead with insurance and commercial as primary HOT signals.
    Storm + insurance = highest ticket of all 4 verticals.
    """
    logger.info("node_score_lead [roofing]")
    try:
        scoring_input = {
            "damage_type":         state.get("damage_type"),
            "urgency":             state.get("urgency"),
            "is_homeowner":        state.get("is_homeowner"),
            "has_insurance":       state.get("has_insurance"),
            "insurance_contacted": state.get("insurance_contacted"),
            "adjuster_involved":   state.get("adjuster_involved"),
            "has_interior_leak":   state.get("has_interior_leak"),
            "property_type":       state.get("property_type"),
            "roof_age":            state.get("roof_age"),
            "email":               bool(state.get("email")),
            "phone":               bool(state.get("phone")),
            "appt_booked":         state.get("appt_booked"),
            "turn_count":          state.get("turn_count"),
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
            # Storm + insurance always HOT even if parsing fails
            if _is_storm_insurance_lead(state):
                state["score"]        = "hot"
                state["score_reason"] = "Storm damage with insurance — auto-scored hot"
            else:
                state["score"]        = "warm"
                state["score_reason"] = "Could not parse scoring output"

    except Exception as e:
        logger.error(f"node_score_lead [roofing] failed: {e}")
        state["score"]        = "hot" if _is_storm_insurance_lead(state) else "warm"
        state["score_reason"] = f"Scoring error: {str(e)}"

    return state


def node_generate_summary(state: dict) -> dict:
    """
    Two summaries: client email + internal Sheets note.
    Internal note flags insurance involvement and commercial status explicitly.
    """
    logger.info("node_generate_summary [roofing]")

    context = {
        "name":                state.get("name"),
        "damage_type":         state.get("damage_type"),
        "damage_detail":       state.get("damage_detail"),
        "storm_date":          state.get("storm_date"),
        "location":            state.get("location"),
        "roof_age":            state.get("roof_age"),
        "has_insurance":       state.get("has_insurance"),
        "insurance_contacted": state.get("insurance_contacted"),
        "adjuster_involved":   state.get("adjuster_involved"),
        "has_interior_leak":   state.get("has_interior_leak"),
        "property_type":       state.get("property_type"),
        "appt_confirmed":      state.get("appt_confirmed"),
        "score":               state.get("score"),
        "score_reason":        state.get("score_reason"),
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
        logger.error(f"node_generate_summary (client) [roofing] failed: {e}")
        appt = state.get("appt_confirmed", "to be scheduled")
        state["summary"] = (
            f"We discussed your {state.get('damage_type', 'roof')} issue "
            f"in {state.get('location', 'your area')}. "
            f"Inspection: {appt}."
        )

    # Internal summary
    try:
        response = llm.invoke([
            SystemMessage(content=SUMMARY_INTERNAL_SYSTEM),
            HumanMessage(content=context_str),
        ], max_tokens=200, temperature=0.3)
        state["internal_summary"] = response.content.strip()
    except Exception as e:
        logger.error(f"node_generate_summary (internal) [roofing] failed: {e}")
        ins  = "INSURANCE" if state.get("has_insurance") else ""
        comm = "COMMERCIAL" if _is_commercial(state) else ""
        state["internal_summary"] = (
            f"{(state.get('score') or '').upper()} {ins} {comm} - "
            f"{state.get('damage_type')} | {state.get('score_reason')}"
        ).strip()

    return state


def node_send_email(state: dict) -> dict:
    """
    Sends inspection confirmation email.
    Storm + insurance path: includes claim guidance section.
    Commercial path: mentions multi-unit scope.
    """
    logger.info("node_send_email [roofing]")

    if not state.get("email"):
        logger.info("No email — skipping")
        return state

    try:
        name         = state.get("name", "there")
        is_storm_ins = _is_storm_insurance_lead(state)
        is_comm      = _is_commercial(state)

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
                <p style="margin:4px 0;color:#555;">
                    Free roof inspection with full photo documentation.
                </p>
                <p style="margin:4px 0;color:#555;">
                    Our inspector calls 30 minutes before arrival.
                    No work begins without your approval.
                </p>
            </div>
            """
        else:
            appt_section = f"""
            <div style="background:#fefce8;border:1px solid #fde047;
                        border-radius:8px;padding:16px;margin:16px 0;">
                <p style="margin:0;">
                    Reply to this email or call
                    <strong>{settings.BUSINESS_PHONE}</strong>
                    to schedule your free inspection.
                </p>
            </div>
            """

        # Insurance guidance — storm leads only
        insurance_section = ""
        if is_storm_ins:
            insurance_section = """
            <div style="background:#eff6ff;border:1px solid #93c5fd;
                        border-radius:8px;padding:16px;margin:16px 0;">
                <h3 style="margin:0 0 8px;color:#1e40af;">
                    About Your Insurance Claim
                </h3>
                <p style="margin:4px 0;color:#555;">
                    Our inspector will document all storm damage with photos
                    and measurements — exactly what your adjuster needs.
                    We work directly with insurance adjusters and can guide
                    you through every step of the claims process.
                </p>
                <p style="margin:8px 0 0;color:#555;">
                    If you have your policy number handy, bring it to the
                    inspection. It will speed up the process.
                </p>
            </div>
            """

        # Commercial note
        commercial_section = ""
        if is_comm:
            commercial_section = """
            <div style="background:#f5f3ff;border:1px solid #c4b5fd;
                        border-radius:8px;padding:16px;margin:16px 0;">
                <p style="margin:0;color:#555;">
                    For commercial properties, our inspector will assess
                    all roofing sections and provide a comprehensive scope
                    report before any quote is generated.
                </p>
            </div>
            """

        subject = (
            "Your roof inspection + insurance claim guidance"
            if is_storm_ins
            else "Your roof inspection is confirmed"
        )

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family:sans-serif;max-width:600px;
                     margin:0 auto;padding:24px;color:#1a1a1a;">
            <h2 style="color:#0D1B2A;">Your Roof Inspection Summary</h2>
            <p>Hi {name},</p>
            <p>{state.get("summary", "Here is a summary of your roof inspection details.")}</p>
            {appt_section}
            {insurance_section}
            {commercial_section}
            <hr style="border:none;border-top:1px solid #e5e4e2;margin:24px 0;">
            <p style="color:#666;font-size:13px;">
                Questions? Call <strong>{settings.BUSINESS_PHONE}</strong>.<br>
                automedge Roofing Team
            </p>
        </body>
        </html>
        """

        result = email_tool.send_email(
            to=state["email"],
            subject=subject,
            html=html_body,
            from_name="automedge Roofing",
        )
        state["email_sent"] = result.get("status") == "sent"
        logger.info(f"Email sent={state['email_sent']} to {state['email']}")

    except Exception as e:
        logger.error(f"node_send_email [roofing] failed: {e}")
        state["email_sent"] = False

    return state


def node_save_sheets(state: dict) -> dict:
    """Saves to correct Google Sheet tab with roofing-specific columns."""
    logger.info("node_save_sheets [roofing]")

    TAB_MAP = {"hot": "Hot Leads", "warm": "Warm Leads", "cold": "Cold Leads"}

    try:
        score = state.get("score", "warm")

        row = [
            datetime.now().isoformat(),                          # A Timestamp
            state.get("name") or "",                             # B Name
            state.get("email") or "",                            # C Email
            state.get("phone") or "",                            # D Phone
            state.get("location") or "",                         # E Location
            state.get("damage_type") or "",                      # F Damage Type
            state.get("damage_detail") or "",                    # G Damage Detail
            state.get("storm_date") or "",                       # H Storm Date
            state.get("roof_age") or "",                         # I Roof Age
            str(state.get("has_insurance") or ""),               # J Has Insurance
            str(state.get("insurance_contacted") or ""),         # K Insurance Contacted
            str(state.get("adjuster_involved") or ""),           # L Adjuster Involved
            str(state.get("has_interior_leak") or ""),           # M Interior Leak
            str(state.get("is_homeowner") or ""),                # N Homeowner
            state.get("property_type") or "",                    # O Property Type
            state.get("urgency") or "",                          # P Urgency
            score.upper(),                                       # Q Score
            str(state.get("score_number") or ""),                # R Score Number
            state.get("score_reason") or "",                     # S Score Reason
            str(state.get("appt_booked", False)),                # T Appt Booked
            state.get("appt_confirmed") or "",                   # U Appt DateTime
            str(state.get("sms_sent", False)),                   # V SMS Sent
            str(state.get("email_sent", False)),                 # W Email Sent
            str(state.get("turn_count", 0)),                     # X Chat Turns
            state.get("internal_summary") or "",                 # Y Internal Summary
            state.get("session_id") or "",                       # Z Session ID
        ]

        row_num = sheets_tool.save_lead_to_sheet(
            score=score,
            row=row,
            sheet_id=settings.ROOFING_SHEET_ID,
        )

        state["sheet_row"] = row_num
        state["sheet_tab"] = TAB_MAP.get(score, "Warm Leads")
        logger.info(f"Saved: tab={state['sheet_tab']} row={row_num}")

    except Exception as e:
        logger.error(f"node_save_sheets [roofing] failed: {e}")

    return state