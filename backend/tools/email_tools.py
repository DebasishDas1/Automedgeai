# tools/email_tools.py
# Resend email notifications for captured leads.
from __future__ import annotations

import asyncio
import html as html_lib
import structlog
from core.config import settings

logger = structlog.get_logger(__name__)

_SCORE_COLORS = {"hot": "#E8593C", "warm": "#EF9F27", "cold": "#378ADD"}


class EmailTools:

    def _client(self, app_state=None):
        """
        Pull Resend client from app state (best for performance)
        or re-initialize if running in a standalone context.
        """
        if app_state and hasattr(app_state, "resend") and app_state.resend:
            return app_state.resend

        try:
            import resend
        except ImportError:
            raise RuntimeError("Run: uv add resend")
        
        if settings.RESEND_API_KEY:
            resend.api_key = settings.RESEND_API_KEY
        return resend.Emails

    async def send_lead_notification(self, state: dict, score: str, app_state=None) -> None:
        """Send lead notification email to the business team."""
        if not settings.RESEND_API_KEY:
            logger.warning("email_skip_no_api_key")
            return
        if not settings.TEAM_EMAIL:
            logger.warning("email_skip_no_team_email")
            return

        safe = {
            k: html_lib.escape(str(state.get(k) or "—"))
            for k in ("name", "email", "phone", "issue",
                      "description", "urgency", "address",
                      "ai_summary", "next_step")
        }

        color = _SCORE_COLORS.get(score, "#888")
        score_label = score.upper()

        html_body = f"""
<div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px;">
  <div style="background:{color};color:#fff;padding:12px 20px;border-radius:8px;
              margin-bottom:24px;display:inline-block;font-weight:600;font-size:18px;">
    {score_label} LEAD
  </div>
  <table style="width:100%;border-collapse:collapse;">
    <tr><td style="padding:8px 0;color:#666;width:120px;">Name</td>
        <td style="padding:8px 0;font-weight:500;">{safe['name']}</td></tr>
    <tr><td style="padding:8px 0;color:#666;">Email</td>
        <td style="padding:8px 0;">{safe['email']}</td></tr>
    <tr><td style="padding:8px 0;color:#666;">Phone</td>
        <td style="padding:8px 0;">{safe['phone']}</td></tr>
    <tr><td style="padding:8px 0;color:#666;">Issue</td>
        <td style="padding:8px 0;">{safe['issue']}</td></tr>
    <tr><td style="padding:8px 0;color:#666;">Description</td>
        <td style="padding:8px 0;">{safe['description']}</td></tr>
    <tr><td style="padding:8px 0;color:#666;">Urgency</td>
        <td style="padding:8px 0;">{safe['urgency']}</td></tr>
    <tr><td style="padding:8px 0;color:#666;">Address</td>
        <td style="padding:8px 0;">{safe['address']}</td></tr>
    <tr><td style="padding:8px 0;color:#666;">Next step</td>
        <td style="padding:8px 0;font-weight:500;">{safe['next_step']}</td></tr>
  </table>
  <div style="margin-top:20px;padding:16px;background:#f8f8f8;
              border-radius:8px;font-size:14px;color:#555;">
    <strong>Summary:</strong> {safe['ai_summary']}
  </div>
</div>"""

        try:
            resend_client = self._client(app_state=app_state)
            await asyncio.to_thread(
                resend_client.send,
                {
                    "from": f"Automedge Leads <{settings.EMAIL_FROM}>",
                    "to": [settings.TEAM_EMAIL],
                    "subject": f"[{score_label}] New lead — {safe['name']} ({safe['issue']})",
                    "html": html_body,
                }
            )
            logger.info("email_sent", score=score, recipient_count=1)
        except Exception as exc:
            logger.error(
                "email_send_failed",
                error_type=type(exc).__name__,
            )


email_tools = EmailTools()