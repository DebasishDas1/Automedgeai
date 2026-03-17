# workflows/base.py
# Shared helpers used by ALL vertical nodes.
# Import from here — never redefine in individual nodes.py files.
import json
import logging
from datetime import datetime, timedelta

from langchain_core.messages import HumanMessage, AIMessage

logger   = logging.getLogger(__name__)
_MISSING = object()


# ── Field helpers ─────────────────────────────────────────────────────────────

def field_missing(state: dict, key: str) -> bool:
    """True only if field was never set. bool False is a valid collected value."""
    val = state.get(key, _MISSING)
    return val is _MISSING or val is None


def merge_extracted(state: dict, extracted: dict) -> dict:
    for k, v in extracted.items():
        if v is None:
            continue
        if field_missing(state, k):
            state[k] = v
            logger.debug(f"field captured: {k}={v!r}")
    return state


def parse_json(content: str) -> dict | None:
    """Extract first JSON object from an LLM response. Returns None on failure."""
    s = content.find("{")
    e = content.rfind("}") + 1
    if s == -1 or e == 0:
        return None
    try:
        return json.loads(content[s:e])
    except json.JSONDecodeError as exc:
        logger.warning(f"JSON parse failed: {exc} | snippet: {content[s:s+120]}")
        return None


# ── Message helpers ───────────────────────────────────────────────────────────

def build_lc_messages(state: dict) -> list:
    """Convert state['messages'] → list of LangChain HumanMessage/AIMessage."""
    out = []
    for m in state.get("messages", []):
        role    = m.get("role")
        content = m.get("content", "")
        if role == "user":
            out.append(HumanMessage(content=content))
        elif role == "assistant":
            out.append(AIMessage(content=content))
    return out


def last_user_msg(state: dict) -> str | None:
    """Content of the most recent user message, or None."""
    return next(
        (m["content"] for m in reversed(state.get("messages", []))
         if m.get("role") == "user"),
        None,
    )


def full_transcript(state: dict) -> str:
    """Flat text of entire conversation — used for final extraction pass."""
    return "\n".join(
        f"{m['role'].upper()}: {m['content']}"
        for m in state.get("messages", [])
    )


# ── Appointment slots ─────────────────────────────────────────────────────────

def get_appt_slots() -> list[str]:
    today = datetime.now()
    return [
        (today + timedelta(days=1)).strftime("%A, %b %d at 10:00 AM"),
        (today + timedelta(days=2)).strftime("%A, %b %d at 2:00 PM"),
        (today + timedelta(days=3)).strftime("%A, %b %d at 9:00 AM"),
    ]


# ── Rule-based lead scorer ────────────────────────────────────────────────────
# Replaces URGENCY_CLASSIFY_SYSTEM + LEAD_SCORING_SYSTEM LLM calls (~450 tokens)
# in pest/plumbing/roofing with deterministic, zero-token logic.
# Each vertical has its own keyword sets and signals.

_EMERGENCY_HVAC = {
    "no heat", "no ac", "carbon monoxide", "gas smell",
    "smoke", "no hot water", "system down",
}
_EMERGENCY_PLUMBING = {
    "flooding", "water damage", "burst pipe", "burst", "overflow",
    "sewage", "sewer backup", "no water", "water everywhere",
}
_EMERGENCY_PEST = {
    "termites", "bed bugs", "rodents", "cockroaches", "wasps",
    "bees", "hornets", "rat", "rats", "mice",
}
_EMERGENCY_ROOFING = {
    "active leak", "ceiling leak", "water coming in", "interior leak",
    "storm damage", "missing shingles", "collapsed",
}


def rule_score_lead(state: dict) -> dict:
    """
    Score a lead with zero LLM tokens.
    Handles all 4 verticals via state['vertical'].
    Returns {"score": "hot"|"warm"|"cold", "score_number": int, "score_reason": str,
             "urgency": str}  ← urgency is set here too, replacing node_score_urgency
    """
    vertical      = (state.get("vertical") or "hvac").lower()
    urgency_raw   = (state.get("urgency") or "").lower()
    is_homeowner  = state.get("is_homeowner")
    has_email     = bool(state.get("email"))
    has_phone     = bool(state.get("phone"))
    appt_booked   = bool(state.get("appt_booked"))
    turn_count    = int(state.get("turn_count") or 0)
    issue         = (state.get("issue") or "").lower()
    budget_signal = (state.get("budget_signal") or "").lower()

    score = 50
    notes = []

    # ── Vertical-specific emergency detection ─────────────────────────────────
    if vertical == "hvac":
        emergency = urgency_raw in ("urgent", "emergency") or any(
            kw in issue for kw in _EMERGENCY_HVAC
        )
        urgency_out = "urgent" if emergency else (urgency_raw or "normal")

    elif vertical == "plumbing":
        emergency = urgency_raw == "emergency" or any(
            kw in issue for kw in _EMERGENCY_PLUMBING
        )
        has_water_damage = bool(state.get("has_water_damage"))
        if emergency or has_water_damage:
            urgency_out = "emergency"
            score += 10  # extra for plumbing emergency severity
        elif urgency_raw == "urgent":
            urgency_out = "urgent"
        else:
            urgency_out = "routine"

    elif vertical == "pest_control":
        pest = (state.get("pest_type") or "").lower()
        has_damage = bool(state.get("has_damage"))
        if pest in _EMERGENCY_PEST or has_damage:
            urgency_out = "high"
            emergency   = True
        elif pest in {"ants", "fleas", "mosquitoes"}:
            urgency_out = "medium"
            emergency   = False
        else:
            urgency_out = "low"
            emergency   = False

    elif vertical == "roofing":
        damage_type = (state.get("damage_type") or "").lower()
        has_interior_leak = bool(state.get("has_interior_leak"))
        if damage_type == "storm" or has_interior_leak or any(
            kw in issue for kw in _EMERGENCY_ROOFING
        ):
            urgency_out = "storm_damage" if damage_type == "storm" else "leak_active"
            emergency   = True
        elif damage_type == "wear":
            urgency_out = "inspection_needed"
            emergency   = False
        else:
            urgency_out = "planning"
            emergency   = False

    else:
        emergency   = urgency_raw in ("urgent", "emergency")
        urgency_out = urgency_raw or "normal"

    # ── Universal scoring signals ─────────────────────────────────────────────
    if emergency:         score += 25; notes.append("emergency")
    if is_homeowner:      score += 10; notes.append("homeowner")
    if has_email:         score +=  5; notes.append("email")
    if has_phone:         score +=  5; notes.append("phone")
    if appt_booked:       score += 15; notes.append("appt booked")
    if turn_count >= 6:   score +=  5; notes.append(f"{turn_count} turns")

    # Vertical-specific bonuses
    if vertical == "pest_control" and state.get("wants_annual"):
        score += 10; notes.append("wants annual plan")
    if vertical == "roofing" and state.get("has_insurance"):
        score +=  8; notes.append("has insurance")
    if vertical == "plumbing" and state.get("has_water_damage"):
        score += 10; notes.append("water damage")

    # Negative signals
    if budget_signal == "price shopping": score -= 20; notes.append("price shopping")
    if is_homeowner is False:             score -= 25; notes.append("renter")
    if not has_email and not has_phone:   score -= 15; notes.append("no contact")
    if turn_count < 3:                    score -= 10; notes.append("low engagement")

    score = max(0, min(100, score))

    if score >= 70:   label = "hot"
    elif score >= 35: label = "warm"
    else:             label = "cold"

    reason = f"{label.upper()}: {', '.join(notes) if notes else 'standard lead'}."
    return {
        "score":        label,
        "score_number": score,
        "score_reason": reason,
        "urgency":      urgency_out,
    }