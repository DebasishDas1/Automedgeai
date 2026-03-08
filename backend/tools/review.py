import logging
from tools.email import email_tool
from tools.sms import sms_tool

logger = logging.getLogger(__name__)

class ReviewTool:
    def request_review(self, name: str, email: str, phone: str = None) -> bool:
        """
        Sends a review request via Email and optionally SMS.
        """
        subject = "How did we do? Rate your service"
        html = f"<h3>Hi {name},</h3><p>Thank you for choosing Automedge. We'd love to hear your feedback.</p><p><a href='https://automedge.com/review'>Leave a review</a></p>"
        
        email_sent = email_tool.send_email(email, subject, html)
        
        sms_sent = False
        if phone:
            sms_message = f"Hi {name}, thanks for your business! Please rate our service here: https://automedge.com/review"
            sms_sent = sms_tool.send_sms(phone, sms_message)
            
        return email_sent or sms_sent

review_tool = ReviewTool()
