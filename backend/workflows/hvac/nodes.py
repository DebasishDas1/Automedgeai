from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from workflows.base import LeadState, add_event
from workflows.hvac.prompts import URGENCY_SYSTEM, URGENCY_USER
from core.config import settings
from tools.notify import notify_tool
import logging
from llm import llm

logger = logging.getLogger(__name__)


def score_urgency(state: LeadState) -> LeadState:
    logger.info(f"Node [score_urgency] for issue: {state['issue']}")
    
    # AI Classification
    system_msg = SystemMessage(content=URGENCY_SYSTEM)
    user_msg = HumanMessage(content=URGENCY_USER.format(issue=state['issue'], city=state['city']))
    
    response = llm.invoke([system_msg, user_msg])
    urgency = response.content.strip().lower()
    
    # Validation
    if urgency not in ["emergency", "urgent", "normal"]:
        urgency = "normal"
    
    state['urgency'] = urgency
    add_event(state, f"Urgency Scored: {urgency.upper()}", "done")
    return state

def dispatch_tech(state: LeadState) -> LeadState:
    logger.info(f"Node [dispatch_tech] for {state['urgency']} lead")
    
    # Only notify tech automatically for emergency/urgent
    if state['urgency'] in ["emergency", "urgent"]:
        lead_info = f"{state['name']} - {state['issue']}"
        success = notify_tool.notify_technician(state['vertical'], state['city'], lead_info)
        state['tech_notified'] = success
        add_event(state, "Technician Dispatched", "done" if success else "error")
    else:
        add_event(state, "Dispatched to Route Queue", "done")
        state['tech_notified'] = False
        
    return state

def book_appointment(state: LeadState) -> LeadState:
    logger.info(f"Node [book_appointment] for {state['name']}")
    
    # In a real app, this might interact with a calendar service
    # For now, we update the stage
    state['stage'] = "booked"
    add_event(state, "Appointment Booked", "done")
    return state
