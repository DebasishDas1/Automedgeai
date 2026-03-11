import logging
import resend
from core.config import settings

logger = logging.getLogger(__name__)


class EmailTool:

    def send_email(self, to: str, subject: str, html_body: str) -> dict:

        # Dev mode mock
        if settings.ENVIRONMENT != "production":
            logger.info(f"[MOCK EMAIL]\nto={to}\nsubject={subject}")
            return {"id": "mock_email", "status": "sent"}

        try:
            resend.api_key = settings.RESEND_API_KEY

            response = resend.Emails.send({
                "from": settings.EMAIL_FROM,
                "to": [to],
                "subject": subject,
                "html": html_body,
            })

            logger.info(f"Email sent via Resend → id={response['id']}")

            return {
                "id": response["id"],
                "status": "sent"
            }

        except Exception as e:
            logger.exception("Email sending failed")
            return {
                "id": None,
                "status": "failed",
                "error": str(e)
            }


# exported tool instance
email_tool = EmailTool()