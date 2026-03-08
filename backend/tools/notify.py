import logging
from tools.sms import sms_tool

logger = logging.getLogger(__name__)

class NotifyTool:
    def notify_technician(self, vertical: str, city: str, lead_info: str) -> bool:
        """
        Simulates notifying the nearest technician.
        In a real app, this would lookup a technician in the DB based on city/vertical.
        """
        # Mock technician pool
        tech_phones = {
            "hvac": "+15551234567",
            "roofing": "+15557654321",
            "plumbing": "+15551112222",
            "pest_control": "+15553334444"
        }
        
        phone = tech_phones.get(vertical, "+15550000000")
        message = f"NEW LEAD ALERT ({vertical.upper()}): {lead_info} in {city}. Reply YES to accept."
        
        logger.info(f"Notifying tech for {vertical} in {city} at {phone}")
        return sms_tool.send_sms(phone, message)

notify_tool = NotifyTool()
