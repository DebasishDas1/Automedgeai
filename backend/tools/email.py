import resend
from core.config import settings
import logging

logger = logging.getLogger(__name__)

class EmailTool:
    def __init__(self):
        resend.api_key = settings.RESEND_API_KEY

    def send_email(self, to: str, subject: str, html: str) -> bool:
        try:
            params = {
                "from": "Automedge <no-reply@automedge.com>",
                "to": [to],
                "subject": subject,
                "html": html,
            }
            resend.Emails.send(params)
            logger.info(f"Email sent to {to}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            return False

email_tool = EmailTool()
