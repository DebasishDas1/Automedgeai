# workflows/roofing/state.py
from __future__ import annotations
from typing import List, Optional, Literal
from typing_extensions import TypedDict


class RoofingState(TypedDict, total=False):
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
    # Roofing-specific collected fields
    damage_type:          Optional[str]   # storm | wear | unknown
    damage_detail:        Optional[str]   # specific description
    storm_date:           Optional[str]
    roof_age:             Optional[str]
    has_interior_leak:    Optional[bool]
    has_insurance:        Optional[bool]
    insurance_contacted:  Optional[bool]
    adjuster_involved:    Optional[bool]
    is_homeowner:         Optional[bool]
    property_type:        Optional[str]   # residential | commercial
    address:              Optional[str]
    # AI assessment
    urgency:       Optional[str]   # storm_damage|leak_active|inspection_needed|planning
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