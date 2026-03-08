from workflows.base import LeadState, add_event
import logging

logger = logging.getLogger(__name__)

def score_urgency(state: LeadState) -> LeadState:
    logger.info(f"Node [score_urgency] (STUB) for {state['vertical']}")
    state['urgency'] = "normal"
    add_event(state, "Urgency Scored: NORMAL", "done")
    return state

def dispatch_tech(state: LeadState) -> LeadState:
    logger.info(f"Node [dispatch_tech] (STUB) for {state['vertical']}")
    state['tech_notified'] = False
    add_event(state, "Added to Route Queue", "done")
    return state

def book_appointment(state: LeadState) -> LeadState:
    logger.info(f"Node [book_appointment] (STUB) for {state['vertical']}")
    state['stage'] = "booked"
    add_event(state, "Appointment Booked", "done")
    return state
