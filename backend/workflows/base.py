# workflows/base.py
# Shared helpers used by ALL vertical nodes.
# Import from here instead of redefining in each vertical's nodes.py.
#
# What lives here:
#   - State helpers (_field_missing, _merge_extracted, etc.)
#   - LangChain message conversion
#   - Appointment slot generation
#   - _parse_json_from_llm
#   - rule_score_lead  ← replaces the 607-token LLM scoring call
#
# What does NOT live here:
#   - Tool imports (sheets/sms/review) — import lazily in the node that needs them
#   - LeadState TypedDict — removed (use ChatState from workflows/state.py)
import json
import logging
from datetime import datetime, timedelta

from langchain_core.messages import HumanMessage, AIMessage

logger   = logging.getLogger(__name__)
_MISSING = object()   # sentinel: distinguishes None from "never set"


# ── Field helpers ─────────────────────────────────────────────────────────────

def field_missing(state: dict, key: str) -> bool:
    """True only if field was never set. bool False is a valid collected value."""
    val = state.get(key, _MISSING)
    return val is _MISSING or val is None


def merge_extracted(state: dict, extracted: dict) -> dict:
    """
    Merge LLM-extracted fields into state.
    First-capture wins — never overwrites an already-set value.
    """
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
    """Three concrete appointment slot strings, starting tomorrow."""
    today = datetime.now()
    return [
        (today + timedelta(days=1)).strftime("%A, %b %d at 10:00 AM"),
        (today + timedelta(days=2)).strftime("%A, %b %d at 2:00 PM"),
        (today + timedelta(days=3)).strftime("%A, %b %d at 9:00 AM"),
    ]


# ── Rule-based lead scorer ────────────────────────────────────────────────────
# Replaces the 607-token LEAD_SCORING_SYSTEM LLM call with deterministic logic.
# Saves ~750 tokens per post-chat run. Scores are consistent and debuggable.

_EMERGENCY_KEYWORDS = {
    "no heat", "no ac", "carbon monoxide", "gas smell", "flooding",
    "water damage", "burst pipe", "smoke", "fire", "no hot water",
}

def rule_score_lead(state: dict) -> dict:
    """
    Score a lead without an LLM call.
    Returns {"score": "hot"|"warm"|"cold", "score_number": int, "score_reason": str}
    """
    urgency        = (state.get("urgency") or "").lower()
    is_homeowner   = state.get("is_homeowner")
    has_email      = bool(state.get("email"))
    has_phone      = bool(state.get("phone"))
    appt_booked    = bool(state.get("appt_booked"))
    turn_count     = int(state.get("turn_count") or 0)
    issue          = (state.get("issue") or "").lower()
    budget_signal  = (state.get("budget_signal") or "").lower()

    score  = 50   # base
    notes  = []

    # ── Positive signals ──────────────────────────────────────────────────────
    emergency = urgency == "urgent" or any(kw in issue for kw in _EMERGENCY_KEYWORDS)
    if emergency:           score += 25; notes.append("emergency")
    if is_homeowner:        score += 10; notes.append("homeowner")
    if has_email:           score +=  5; notes.append("email")
    if has_phone:           score +=  5; notes.append("phone")
    if appt_booked:         score += 15; notes.append("appt booked")
    if turn_count >= 6:     score +=  5; notes.append(f"{turn_count} turns")
    if urgency == "this week": score += 5; notes.append("this week")

    # ── Negative signals ──────────────────────────────────────────────────────
    if budget_signal == "price shopping": score -= 20; notes.append("price shopping")
    if is_homeowner is False:             score -= 25; notes.append("renter")
    if not has_email and not has_phone:   score -= 15; notes.append("no contact")
    if turn_count < 3:                   score -= 10; notes.append("low engagement")

    score = max(0, min(100, score))

    if score >= 70:
        label = "hot"
    elif score >= 35:
        label = "warm"
    else:
        label = "cold"

    reason = f"{label.upper()}: {', '.join(notes) if notes else 'standard lead'}."
    return {"score": label, "score_number": score, "score_reason": reason}