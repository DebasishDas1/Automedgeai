# workflows/pest_control/state.py
from __future__ import annotations
from typing import List, Optional, Literal
from typing_extensions import TypedDict


class PestState(TypedDict, total=False):
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
    # Pest-specific collected fields
    pest_type:        Optional[str]   # termites|bed bugs|rodents|ants|cockroaches|spiders|wasps|mosquitoes|fleas
    infestation_area: Optional[str]
    duration:         Optional[str]
    has_damage:       Optional[bool]
    tried_treatment:  Optional[bool]
    is_homeowner:     Optional[bool]
    wants_annual:     Optional[bool]
    property_type:    Optional[str]   # house|apartment|commercial
    address:          Optional[str]
    # AI assessment
    urgency:       Optional[str]   # high|medium|low — explicit user input
    ai_urgency:    Optional[str]   # classification assessment
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