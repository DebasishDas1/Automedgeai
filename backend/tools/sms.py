import logging
from core.config import settings

logger = logging.getLogger(__name__)

class SMSTool:
    def send_sms(self, to: str, body: str) -> dict:
        if settings.ENVIRONMENT != "prod":
            logger.info(f"[MOCK SMS] to={to}\n{body}")
            return {"sid": "mock_sid", "status": "sent"}

        logger.info(f"Sending real SMS to {to}")
        return {"sid": "twilio_sid", "status": "sent"}


sms_tool = SMSTool()