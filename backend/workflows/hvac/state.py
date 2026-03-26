# workflows/hvac/state.py
from __future__ import annotations
from typing import List, Optional, Literal
from typing_extensions import TypedDict


class HvacState(TypedDict, total=False):
    # Session
    session_id:    str
    request_id:    Optional[str]
    vertical:      Literal["hvac", "plumbing", "roofing", "pest_control"]
    # Conversation
    messages:      List[dict]
    turn_count:    int
    is_complete:   bool
    # Collected contact fields — all start as None in workflow_tools
    name:          Optional[str]
    email:         Optional[str]
    phone:         Optional[str]
    issue:         Optional[str]
    description:   Optional[str]   # detailed symptom description
    urgency:       Optional[str]   # explicit user-stated urgency only
    address:       Optional[str]   # city / zip / full address
    is_homeowner:  Optional[bool]
    budget_signal: Optional[str]
    # AI assessment fields (not collected fields — not used for is_complete)
    ai_urgency:    Optional[str]   # classification assessment
    intent:        Optional[str]
    is_spam:       Optional[bool]
    ai_summary:    Optional[str]
    # Scoring
    score:         Optional[str]
    score_reason:  Optional[str]
    next_step:     Optional[str]
    # Appointment
    appt_slots:    Optional[List[str]]
    appt_booked:   Optional[bool]
    appt_confirmed:Optional[str]
    # Metadata
    last_node:     Optional[str]
    error:         Optional[str]
    duration_ms:   Optional[int]