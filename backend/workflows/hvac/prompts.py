URGENCY_SYSTEM = """
You are an HVAC dispatch classifier for a US-based
home services company. Classify inbound service
requests by urgency level only.
"""

URGENCY_USER = """
Customer issue: {issue}
Customer city:  {city}

Urgency levels:
  emergency = gas leak, carbon monoxide, flooding,
              no heat below 40°F, electrical sparks
  urgent    = AC out above 90°F, no hot water,
              heat out above 60°F
  normal    = routine maintenance, general inquiry,
              system making noise, efficiency concern

Respond with exactly one word: emergency, urgent, or normal
"""

SMS_FIRST_CONTACT = """
Hi {name}! This is {tech_name} from {business_name} HVAC.
We received your request about: {issue}.
We'll call you within 5 minutes to confirm your appointment.
Reply STOP to opt out.
"""

SMS_BOOKING_LINK = """
Hi {name}, here is your booking link to pick a time
that works for you: {booking_url}
Takes 30 seconds. Reply STOP to opt out.
"""

SMS_REVIEW_REQUEST = """
Hi {name}! Thanks for choosing {business_name}.
Hope your {issue} is all sorted! If you have 60 seconds,
a Google review means the world to us: {review_url}
"""