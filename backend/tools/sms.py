from twilio.rest import Client
from core.config import settings
import logging

logger = logging.getLogger(__name__)

class SMSTool:
    def __init__(self):
        self._client = None
        self.from_number = settings.TWILIO_FROM_NUMBER

    @property
    def client(self):
        if self._client is None:
            try:
                self._client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
                raise
        return self._client

    def send_sms(self, to: str, message: str) -> bool:
        try:
            message = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to
            )
            logger.info(f"SMS sent to {to}: {message.sid}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS to {to}: {e}")
            return False

sms_tool = SMSTool()
