# workflows/plumbing/state.py
from __future__ import annotations
from typing import List, Optional
from typing_extensions import TypedDict


class PlumbingState(TypedDict, total=False):
    # ── Session ───────────────────────────────────────────────────────────────
    session_id:    str
    vertical:      str

    # ── Conversation ──────────────────────────────────────────────────────────
    messages:      List[dict]
    turn_count:    int
    is_complete:   bool

    # ── Contact (pre-seeded from form) ────────────────────────────────────────
    name:          Optional[str]
    email:         Optional[str]
    phone:         Optional[str]

    # ── Plumbing-specific fields ──────────────────────────────────────────────
    issue:             Optional[str]   # "burst pipe", "slow drain", etc.
    issue_type:        Optional[str]   # "emergency" | "routine"
    problem_area:      Optional[str]   # kitchen | bathroom | basement | whole_house | outside
    has_water_damage:  Optional[bool]
    is_getting_worse:  Optional[bool]
    main_shutoff_off:  Optional[bool]
    is_homeowner:      Optional[bool]
    property_type:     Optional[str]   # house | apartment | commercial
    address:           Optional[str]

    # ── AI assessment ─────────────────────────────────────────────────────────
    urgency:       Optional[str]   # emergency | urgent | routine — explicit user input
    ai_urgency:    Optional[str]   # classification assessment
    intent:        Optional[str]
    is_spam:       Optional[bool]
    ai_summary:    Optional[str]

    # ── Appointment ───────────────────────────────────────────────────────────
    appt_slots:        Optional[List[str]]  # offered time slots
    wants_appointment: Optional[bool]       # user expressed intent to book
    appt_booked:       Optional[bool]       # booking confirmed in session
    appt_confirmed:    Optional[str]        # exact confirmed slot string

    # ── Scoring ───────────────────────────────────────────────────────────────
    score:         Optional[str]
    score_reason:  Optional[str]
    next_step:     Optional[str]

    # ── Metadata ──────────────────────────────────────────────────────────────
    last_node:     Optional[str]
    error:         Optional[str]
    duration_ms:   Optional[int]