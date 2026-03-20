# workflows/plumbing/state.py
from __future__ import annotations
from typing import List, Optional, Literal
from typing_extensions import TypedDict


class PlumbingState(TypedDict, total=False):
    # Session
    session_id:    str
    vertical:      str
    # Conversation
    messages:      List[dict]
    turn_count:    int
    is_complete:   bool
    # Contact (pre-filled from form)
    name:          Optional[str]
    email:         Optional[str]
    phone:         Optional[str]
    # Plumbing-specific collected fields
    issue:         Optional[str]     # brief issue label e.g. "burst pipe", "slow drain"
    issue_type:    Optional[str]     # "emergency" | "routine"
    problem_area:  Optional[str]     # kitchen | bathroom | basement | whole_house | outside
    has_water_damage:  Optional[bool]
    is_getting_worse:  Optional[bool]
    main_shutoff_off:  Optional[bool]
    is_homeowner:      Optional[bool]
    property_type:     Optional[str]  # house | apartment | commercial
    address:           Optional[str]
    # AI assessment
    urgency:       Optional[str]   # emergency | urgent | routine — explicit user input
    ai_urgency:    Optional[str]   # classification assessment only
    intent:        Optional[str]
    is_spam:       Optional[bool]
    ai_summary:    Optional[str]
    # Appointment
    appt_slots:    Optional[List[str]]
    appt_booked:   Optional[bool]
    appt_confirmed:Optional[str]
    # Scoring
    score:         Optional[str]
    score_reason:  Optional[str]
    next_step:     Optional[str]
    # Metadata
    last_node:     Optional[str]
    error:         Optional[str]
    duration_ms:   Optional[int]