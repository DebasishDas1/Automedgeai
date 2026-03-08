import logging
from core.config import settings

logger = logging.getLogger(__name__)

class EmailTool:
    def send_email(to: str, subject: str, html_body: str) -> dict:
        if settings.ENVIRONMENT != "production":
            logger.info(f"[MOCK EMAIL] to={to}\nsubject={subject}")
            return {"id": "mock_id", "status": "sent"}

        logger.info(f"Sending real email to {to}")
        return {"id": "real_id", "status": "sent"}


# exported tool instance
email_tool = EmailTool()