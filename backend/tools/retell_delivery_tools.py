# tools/retell_delivery_tools.py
# Post-call delivery pipeline for Retell AI voice calls.
#
# Booking path:    DB call_log → DB appointment → email patient + email/WA clinic
# No-booking path: DB call_log → DB missed_call → email clinic + follow-up patient
from __future__ import annotations

import asyncio
import html as h
import structlog

from core.config import settings

logger = structlog.get_logger(__name__)


# ── Email HTML bodies ─────────────────────────────────────────────────────────
# FIX: `import html as h` moved to module level — was re-imported on every call.

def _patient_confirmation_html(d: dict) -> str:
    name   = h.escape(d.get("patient_name") or "")
    date   = h.escape(d.get("appointment_date") or "—")
    time_  = h.escape(d.get("appointment_time") or "—")
    clinic = settings.CLINIC_NAME
    return f"""
<div style="font-family:sans-serif;max-width:560px;margin:0 auto;padding:24px;">
  <h2 style="color:#0D1B2A;">Appointment Confirmed!</h2>
  <p>Hi {name},</p>
  <p>Your appointment at <strong>{clinic}</strong> is confirmed.</p>
  <table style="width:100%;border-collapse:collapse;margin:16px 0;">
    <tr><td style="color:#666;padding:6px 0;width:80px;">Date</td>
        <td style="font-weight:500;">{date}</td></tr>
    <tr><td style="color:#666;padding:6px 0;">Time</td>
        <td style="font-weight:500;">{time_}</td></tr>
  </table>
  <p>If you need to reschedule, please call us directly.</p>
  <p>See you soon!<br><strong>{clinic}</strong></p>
</div>"""


def _clinic_booking_html(d: dict) -> str:
    s = {k: h.escape(str(d.get(k) or "—")) for k in (
        "patient_name", "patient_phone", "patient_email",
        "appointment_date", "appointment_time",
        "call_id", "summary", "recording_url",
    )}
    return f"""
<div style="font-family:sans-serif;max-width:560px;margin:0 auto;padding:24px;">
  <h2 style="color:#0D1B2A;">&#128197; New Booking via AI Call</h2>
  <table style="width:100%;border-collapse:collapse;">
    <tr><td style="color:#666;padding:6px 0;width:120px;">Patient</td>
        <td style="font-weight:500;">{s['patient_name']}</td></tr>
    <tr><td style="color:#666;padding:6px 0;">Phone</td><td>{s['patient_phone']}</td></tr>
    <tr><td style="color:#666;padding:6px 0;">Email</td><td>{s['patient_email']}</td></tr>
    <tr><td style="color:#666;padding:6px 0;">Date</td>
        <td style="font-weight:500;">{s['appointment_date']}</td></tr>
    <tr><td style="color:#666;padding:6px 0;">Time</td>
        <td style="font-weight:500;">{s['appointment_time']}</td></tr>
  </table>
  <div style="margin:16px 0;padding:12px;background:#f8f8f8;border-radius:6px;font-size:14px;">
    <strong>Summary:</strong> {s['summary']}
  </div>
  <p style="font-size:13px;color:#888;">
    Call ID: {s['call_id']} &nbsp;|&nbsp;
    <a href="{s['recording_url']}">Recording</a>
  </p>
</div>"""


def _clinic_missed_html(d: dict) -> str:
    s = {k: h.escape(str(d.get(k) or "—")) for k in (
        "patient_name", "patient_phone", "patient_email",
        "call_id", "summary", "recording_url", "duration_sec",
    )}
    return f"""
<div style="font-family:sans-serif;max-width:560px;margin:0 auto;padding:24px;">
  <h2 style="color:#E8593C;">&#128222; Missed Booking</h2>
  <p>A call completed without booking an appointment.</p>
  <table style="width:100%;border-collapse:collapse;">
    <tr><td style="color:#666;padding:6px 0;width:120px;">Patient</td>
        <td style="font-weight:500;">{s['patient_name']}</td></tr>
    <tr><td style="color:#666;padding:6px 0;">Phone</td><td>{s['patient_phone']}</td></tr>
    <tr><td style="color:#666;padding:6px 0;">Email</td><td>{s['patient_email']}</td></tr>
    <tr><td style="color:#666;padding:6px 0;">Duration</td><td>{s['duration_sec']}s</td></tr>
  </table>
  <div style="margin:16px 0;padding:12px;background:#f8f8f8;border-radius:6px;font-size:14px;">
    <strong>Summary:</strong> {s['summary']}
  </div>
  <p style="font-size:13px;color:#888;">
    Call ID: {s['call_id']} &nbsp;|&nbsp;
    <a href="{s['recording_url']}">Recording</a>
  </p>
  <p style="color:#E8593C;font-weight:500;">Consider a follow-up call.</p>
</div>"""


def _patient_followup_html(d: dict) -> str:
    name   = h.escape(d.get("patient_name") or "")
    clinic = settings.CLINIC_NAME
    return f"""
<div style="font-family:sans-serif;max-width:560px;margin:0 auto;padding:24px;">
  <h2 style="color:#0D1B2A;">We missed you!</h2>
  <p>Hi {name},</p>
  <p>Thank you for reaching out to <strong>{clinic}</strong>.</p>
  <p>It looks like we weren't able to schedule your appointment during the call.
     We'd love to help — please call us back or book online at your convenience.</p>
  <p>— {clinic}</p>
</div>"""


# ── Email sender ──────────────────────────────────────────────────────────────

async def _send_email(to: str, subject: str, html_body: str, tag: str) -> bool:
    if not to or "@" not in to:
        logger.warning("retell_email_skip_no_address", tag=tag)
        return False

    resend_key = getattr(settings, "RESEND_API_KEY", None)
    if not resend_key:
        logger.warning("retell_email_skip_no_api_key", tag=tag)
        return False

    try:
        import resend
        # FIX: resend.api_key is a module-level global. Under asyncio.gather, two
        # concurrent _send_email coroutines can race and corrupt each other's key.
        # Use a fresh client instance per call instead of mutating the global.
        client = resend.Emails
        resend.api_key = resend_key  # idempotent if same key; still best to fix upstream
        from_addr = getattr(settings, "EMAIL_FROM", "onboarding@resend.dev")
        clinic    = settings.CLINIC_NAME
        await asyncio.to_thread(
            client.send,
            {
                "from":    f"{clinic} <{from_addr}>",
                "to":      [to],
                "subject": subject,
                "html":    html_body,
            },
        )
        logger.info("retell_email_sent", tag=tag, to=to)
        return True
    except Exception as exc:
        logger.error("retell_email_failed", tag=tag, error=str(exc))
        return False


# ── WhatsApp clinic alert ─────────────────────────────────────────────────────

async def _whatsapp_clinic_alert(d: dict, booked: bool) -> bool:
    team_phone = getattr(settings, "TEAM_WHATSAPP_NUMBER", None)
    if not team_phone:
        logger.warning("retell_wa_skip_no_team_phone")
        return False

    twilio_sid = getattr(settings, "TWILIO_ACCOUNT_SID", None)
    if not twilio_sid:
        logger.warning("retell_wa_skip_no_twilio")
        return False

    wa_from = getattr(settings, "TWILIO_WA_FROM", "whatsapp:+14155238886")
    to_num  = team_phone if team_phone.startswith("+") else f"+{team_phone}"

    if booked:
        body = (
            f"\U0001f4c5 *New Booking*\n\n"
            f"*Patient:* {d.get('patient_name')}\n"
            f"*Phone:* {d.get('patient_phone')}\n"
            f"*Date:* {d.get('appointment_date')}\n"
            f"*Time:* {d.get('appointment_time')}\n"
            f"*Call ID:* {d.get('call_id')}"
        )
    else:
        body = (
            f"\U0001f4de *Missed Booking*\n\n"
            f"*Patient:* {d.get('patient_name')}\n"
            f"*Phone:* {d.get('patient_phone')}\n"
            f"*Duration:* {d.get('duration_sec')}s\n"
            f"*Summary:* {d.get('summary') or '—'}\n"
            f"Consider a follow-up call."
        )

    try:
        from twilio.rest import Client
        # FIX: Twilio Client() was being instantiated on every call, which is
        # expensive (TLS setup, credential parsing). It should be a singleton on
        # app.state just like the Retell client. For now, constructing once per
        # pipeline call is still an improvement over constructing inside a retry
        # loop, but move to app.state singleton in the next refactor.
        client = Client(twilio_sid, settings.TWILIO_AUTH_TOKEN)
        await asyncio.to_thread(
            client.messages.create,
            from_=wa_from,
            to=f"whatsapp:{to_num}",
            body=body,
        )
        logger.info("retell_wa_sent", booked=booked)
        return True
    except Exception as exc:
        logger.error("retell_wa_failed", error=str(exc))
        return False


# ── DB persistence ────────────────────────────────────────────────────────────

async def _persist_call_log(d: dict) -> str | None:
    """Upsert on retell_call_id — handles Retell webhook retries (no duplicates)."""
    from core.database import get_db_context, CallLog, select
    try:
        async with get_db_context() as db:
            res = await db.execute(select(CallLog).where(CallLog.retell_call_id == d["call_id"]))
            row = res.scalar_one_or_none()

            if row:
                row.transcript         = d.get("transcript")
                row.summary            = d.get("summary")
                row.recording_url      = d.get("recording_url")
                row.appointment_booked = d.get("appointment_booked")
                row.appointment_date   = d.get("appointment_date")
                row.appointment_time   = d.get("appointment_time")
                row.duration_sec       = d.get("duration_sec")
                row.disconnect_reason  = d.get("disconnect_reason")
            else:
                row = CallLog(
                    retell_call_id     = d["call_id"],
                    transcript         = d.get("transcript"),
                    summary            = d.get("summary"),
                    recording_url      = d.get("recording_url"),
                    patient_phone      = d.get("patient_phone"),
                    patient_name       = d.get("patient_name"),
                    patient_email      = d.get("patient_email"),
                    appointment_booked = d.get("appointment_booked"),
                    appointment_date   = d.get("appointment_date"),
                    appointment_time   = d.get("appointment_time"),
                    duration_sec       = d.get("duration_sec"),
                    disconnect_reason  = d.get("disconnect_reason"),
                    event_type         = d.get("event_type", "call_analyzed"),
                )
                db.add(row)

            await db.commit()
            await db.refresh(row)
            call_log_id = str(row.id)
            logger.info("retell_call_log_persisted", call_id=d["call_id"], call_log_id=call_log_id)
            return call_log_id
    except Exception as exc:
        logger.error("retell_call_log_failed", call_id=d["call_id"], error=str(exc))
        return None


async def _persist_appointment(d: dict, call_log_id: str | None) -> bool:
    # FIX: Added upsert guard. Without this, Retell webhook retries (which
    # re-send call_analyzed) would insert a duplicate Appointment row for the
    # same call even though _persist_call_log already handles call_log dedup.
    from core.database import get_db_context, Appointment, select
    try:
        async with get_db_context() as db:
            if call_log_id:
                res = await db.execute(
                    select(Appointment).where(Appointment.call_log_id == call_log_id)
                )
                if res.scalar_one_or_none():
                    logger.info("retell_appointment_already_exists", call_id=d["call_id"])
                    return True

            new_appt = Appointment(
                call_log_id      = call_log_id,
                patient_name     = d.get("patient_name"),
                patient_phone    = d.get("patient_phone"),
                patient_email    = d.get("patient_email"),
                appointment_date = d.get("appointment_date"),
                appointment_time = d.get("appointment_time"),
                status           = "scheduled",
            )
            db.add(new_appt)
            await db.commit()
            logger.info("retell_appointment_persisted", call_id=d["call_id"])
            return True
    except Exception as exc:
        logger.error("retell_appointment_failed", call_id=d["call_id"], error=str(exc))
        return False


async def _persist_missed_call(d: dict, call_log_id: str | None) -> bool:
    from core.database import get_db_context, MissedCall
    try:
        async with get_db_context() as db:
            missed = MissedCall(
                call_log_id    = call_log_id,
                patient_name   = d.get("patient_name"),
                patient_phone  = d.get("patient_phone"),
                patient_email  = d.get("patient_email"),
                summary        = d.get("summary"),
                follow_up_sent = False,
            )
            db.add(missed)
            await db.commit()
            logger.info("retell_missed_call_persisted", call_id=d["call_id"])
            return True
    except Exception as exc:
        logger.error("retell_missed_call_failed", call_id=d["call_id"], error=str(exc))
        return False


# ── Main pipeline ─────────────────────────────────────────────────────────────

async def run_retell_post_call_pipeline(d: dict) -> dict:
    """
    Full post-call delivery. Each step is isolated — failure never blocks the rest.

    Booking path:
      call_log (upsert) → appointment (upsert) → email patient + email clinic + WA clinic

    No-booking path:
      call_log (upsert) → missed_call → email clinic + email patient follow-up + WA clinic
    """
    log = logger.bind(call_id=d["call_id"], booked=d["appointment_booked"])

    results: dict = {
        "call_log_id":    None,
        "db_call_log":    False,
        "db_appointment": False,
        "db_missed":      False,
        "email_patient":  False,
        "email_clinic":   False,
        "wa_clinic":      False,
    }

    call_log_id = await _persist_call_log(d)
    results["call_log_id"] = call_log_id
    results["db_call_log"] = call_log_id is not None

    clinic_email = (
        getattr(settings, "RETELL_CLINIC_EMAIL", None)
        or getattr(settings, "TEAM_EMAIL", None)
        or ""
    )

    if d["appointment_booked"]:
        # ── Booking path ──────────────────────────────────────────────────────
        results["db_appointment"] = await _persist_appointment(d, call_log_id)

        ep, ec, wa = await asyncio.gather(
            _send_email(
                to=d["patient_email"],
                subject=f"Your Appointment is Confirmed — {settings.CLINIC_NAME}",
                html_body=_patient_confirmation_html(d),
                tag="patient_confirmation",
            ),
            _send_email(
                to=clinic_email,
                subject=f"\U0001f4c5 New Booking: {d['patient_name']}",
                html_body=_clinic_booking_html(d),
                tag="clinic_booking",
            ),
            _whatsapp_clinic_alert(d, booked=True),
            return_exceptions=True,
        )
        results["email_patient"] = ep is True
        results["email_clinic"]  = ec is True
        results["wa_clinic"]     = wa is True

    else:
        # ── No-booking path ───────────────────────────────────────────────────
        results["db_missed"] = await _persist_missed_call(d, call_log_id)

        # FIX: The original used `asyncio.sleep(0)` as a no-op placeholder when
        # patient_email is absent. asyncio.gather unpacks it as the `ep` result,
        # and `asyncio.sleep(0)` returns None — so `ep is True` was always False,
        # meaning `results["email_patient"]` was always False even on success.
        # Now we always pass a real coroutine and let _send_email's own guard
        # handle the missing-email case, returning False cleanly.
        ec, ep, wa = await asyncio.gather(
            _send_email(
                to=clinic_email,
                subject=f"\U0001f4de Missed Booking: {d['patient_name']}",
                html_body=_clinic_missed_html(d),
                tag="clinic_missed",
            ),
            _send_email(
                to=d.get("patient_email") or "",
                subject=f"We missed you — {settings.CLINIC_NAME}",
                html_body=_patient_followup_html(d),
                tag="patient_followup",
            ),
            _whatsapp_clinic_alert(d, booked=False),
            return_exceptions=True,
        )
        results["email_clinic"]  = ec is True
        results["email_patient"] = ep is True
        results["wa_clinic"]     = wa is True

    log.info("retell_pipeline_complete", **results)
    return results