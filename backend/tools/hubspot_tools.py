# tools/hubspot_tools.py
# HubSpot CRM integration — contacts, deals, and meetings.
# Requires: uv add hubspot-api-client
# Env vars: HUBSPOT_ACCESS_TOKEN (private app token)
#           HUBSPOT_PIPELINE_ID, HUBSPOT_STAGE_HOT/WARM/COLD (optional overrides)
from __future__ import annotations

import asyncio
import structlog
from datetime import datetime, timezone, timedelta
from typing import Optional

from core.config import settings

logger = structlog.get_logger(__name__)

# ── Client singleton ──────────────────────────────────────────────────────────
# One HubSpot client for the process lifetime — avoids rebuilding the
# connection pool on every function call.

_hs_client = None


def _client():
    global _hs_client
    if _hs_client is not None:
        return _hs_client
    try:
        from hubspot import HubSpot
    except ImportError:
        raise RuntimeError("Run: uv add hubspot-api-client")
    token = settings.HUBSPOT_ACCESS_TOKEN
    if not token:
        raise RuntimeError("HUBSPOT_ACCESS_TOKEN env var not set")
    _hs_client = HubSpot(access_token=token)
    return _hs_client


# ── Helpers ───────────────────────────────────────────────────────────────────

def _phone_clean(phone: str | None) -> str | None:
    """Normalize phone to E.164 digits only."""
    if not phone:
        return None
    digits = "".join(c for c in phone if c.isdigit())
    return f"+{digits}" if digits else None


def _score_to_hs_stage(score: str | None) -> str:
    """
    Map internal lead score to HubSpot pipeline stage ID.

    Stage IDs come from config so they can be overridden per-account
    without a code change. Defaults match HubSpot's built-in sales pipeline.
    Check your actual IDs at: Settings → CRM → Pipelines.
    """
    stage_map = {
        "hot":  getattr(settings, "HUBSPOT_STAGE_HOT",  "appointmentscheduled"),
        "warm": getattr(settings, "HUBSPOT_STAGE_WARM", "qualifiedtobuy"),
        "cold": getattr(settings, "HUBSPOT_STAGE_COLD", "presentationscheduled"),
    }
    return stage_map.get(score or "warm", stage_map["warm"])


def _pipeline_id() -> str:
    return getattr(settings, "HUBSPOT_PIPELINE_ID", "default")


def _issue_field(state: dict) -> str:
    """Resolve the issue field across all verticals."""
    return (
        state.get("issue")
        or state.get("pest_type")
        or state.get("damage_type")
        or ""
    )


# ── 1. Upsert contact ─────────────────────────────────────────────────────────

async def upsert_contact(state: dict) -> Optional[str]:
    """
    Create or update a HubSpot contact by email.
    Returns the HubSpot contact ID, or None on failure.

    Custom contact properties required in HubSpot (Settings → Properties → Contact):
        automedge_vertical, automedge_issue, automedge_urgency,
        automedge_score, automedge_summary, automedge_session_id
    """
    log = logger.bind(service="hubspot_upsert_contact",
                      session_id=state.get("session_id"))

    email = state.get("email")
    name  = (state.get("name") or "").strip()
    parts = name.split(" ", 1)
    first = parts[0]
    last  = parts[1] if len(parts) > 1 else ""

    props = {
        "firstname":            first,
        "lastname":             last,
        "phone":                _phone_clean(state.get("phone")) or "",
        "address":              state.get("address") or "",
        "hs_lead_status":       "NEW",
        "automedge_vertical":   state.get("vertical", ""),
        "automedge_issue":      _issue_field(state),
        "automedge_urgency":    state.get("urgency") or state.get("ai_urgency") or "",
        "automedge_score":      state.get("score") or "",
        "automedge_summary":    state.get("ai_summary") or "",
        "automedge_session_id": state.get("session_id") or "",
    }
    if email:
        props["email"] = email

    try:
        api = _client()

        # Try update-by-email first to avoid duplicates
        if email:
            try:
                from hubspot.crm.contacts import PublicObjectSearchRequest
                search_resp = await asyncio.to_thread(
                    api.crm.contacts.search_api.do_search,
                    public_object_search_request=PublicObjectSearchRequest(
                        filter_groups=[{
                            "filters": [{
                                "property_name": "email",
                                "operator":      "EQ",
                                "value":         email,
                            }]
                        }],
                        properties=["id"],
                        limit=1,
                    ),
                )
                if search_resp.results:
                    contact_id = search_resp.results[0].id
                    from hubspot.crm.contacts import SimplePublicObjectInput
                    await asyncio.to_thread(
                        api.crm.contacts.basic_api.update,
                        contact_id=contact_id,
                        simple_public_object_input=SimplePublicObjectInput(
                            properties=props
                        ),
                    )
                    log.info("contact_updated", contact_id=contact_id)
                    return contact_id
            except Exception as exc:
                # Log and fall through to create — don't swallow silently
                log.warning("contact_search_failed_falling_through_to_create",
                            error=str(exc))

        # Create new contact
        from hubspot.crm.contacts import SimplePublicObjectInputForCreate
        result = await asyncio.to_thread(
            api.crm.contacts.basic_api.create,
            simple_public_object_input_for_create=SimplePublicObjectInputForCreate(
                properties=props
            ),
        )
        contact_id = result.id
        log.info("contact_created", contact_id=contact_id)
        return contact_id

    except Exception as exc:
        log.error("upsert_contact_failed", error=str(exc))
        return None


# ── 2. Create deal ────────────────────────────────────────────────────────────

async def create_deal(state: dict, contact_id: str) -> Optional[str]:
    """
    Create a HubSpot deal and associate it with the contact.
    Returns the deal ID, or None on failure.

    Custom deal properties required in HubSpot (Settings → Properties → Deal):
        automedge_score, automedge_vertical
    """
    log = logger.bind(service="hubspot_create_deal",
                      session_id=state.get("session_id"))

    vertical  = state.get("vertical", "hvac").replace("_", " ").title()
    issue     = _issue_field(state) or "Service Request"
    score     = state.get("score") or "warm"
    name      = state.get("name") or "Lead"
    address   = state.get("address") or ""

    deal_name = f"{vertical} — {issue} ({name})"
    if address:
        deal_name += f" — {address}"

    props = {
        "dealname":           deal_name,
        "dealstage":          _score_to_hs_stage(score),
        "pipeline":           _pipeline_id(),
        "description":        state.get("ai_summary") or "",
        "automedge_score":    score,
        "automedge_vertical": state.get("vertical", ""),
    }

    # Insurance roofing leads get a conservative deal value for pipeline weighting
    if state.get("vertical") == "roofing" and state.get("has_insurance"):
        props["amount"] = "15000"

    try:
        api = _client()
        from hubspot.crm.deals import SimplePublicObjectInputForCreate

        result = await asyncio.to_thread(
            api.crm.deals.basic_api.create,
            simple_public_object_input_for_create=SimplePublicObjectInputForCreate(
                properties=props
            ),
        )
        deal_id = result.id

        # Associate deal → contact using the v4 default association
        # (avoids magic string type IDs required by v3)
        await asyncio.to_thread(
            api.crm.associations.v4.basic_api.create_default,
            object_type="deals",
            object_id=deal_id,
            to_object_type="contacts",
            to_object_id=contact_id,
        )

        log.info("deal_created", deal_id=deal_id, score=score)
        return deal_id

    except Exception as exc:
        log.error("create_deal_failed", error=str(exc))
        return None


# ── 3. Update contact / deal ──────────────────────────────────────────────────

async def update_contact(contact_id: str, updates: dict) -> bool:
    """Update arbitrary properties on an existing HubSpot contact."""
    log = logger.bind(service="hubspot_update_contact", contact_id=contact_id)
    try:
        from hubspot.crm.contacts import SimplePublicObjectInput
        api = _client()
        await asyncio.to_thread(
            api.crm.contacts.basic_api.update,
            contact_id=contact_id,
            simple_public_object_input=SimplePublicObjectInput(properties=updates),
        )
        log.info("contact_props_updated", fields=list(updates.keys()))
        return True
    except Exception as exc:
        log.error("update_contact_failed", error=str(exc))
        return False


async def update_deal(deal_id: str, updates: dict) -> bool:
    """Update arbitrary properties on an existing HubSpot deal."""
    log = logger.bind(service="hubspot_update_deal", deal_id=deal_id)
    try:
        from hubspot.crm.deals import SimplePublicObjectInput
        api = _client()
        await asyncio.to_thread(
            api.crm.deals.basic_api.update,
            deal_id=deal_id,
            simple_public_object_input=SimplePublicObjectInput(properties=updates),
        )
        log.info("deal_props_updated", fields=list(updates.keys()))
        return True
    except Exception as exc:
        log.error("update_deal_failed", error=str(exc))
        return False


# ── 4. Book meeting ───────────────────────────────────────────────────────────

async def book_meeting(
    state: dict,
    contact_id: str,
    slot_str: str | None = None,
) -> Optional[str]:
    """
    Create a HubSpot meeting engagement and link it to the contact.
    Returns the meeting ID, or None on failure.
    """
    log = logger.bind(service="hubspot_book_meeting",
                      session_id=state.get("session_id"))

    slot = slot_str or (
        state.get("appt_slots", [None])[0] if state.get("appt_slots") else None
    )
    start_ms = _parse_slot_to_ms(slot)
    end_ms   = start_ms + 3_600_000  # 1-hour window

    vertical = state.get("vertical", "hvac").replace("_", " ").title()
    issue    = _issue_field(state) or "service request"
    name     = state.get("name") or "Customer"
    address  = state.get("address") or ""

    title = f"{vertical} Inspection — {name}"
    if address:
        title += f" @ {address}"

    body = (
        f"Vertical: {vertical}\n"
        f"Issue: {issue}\n"
        f"Address: {address}\n"
        f"Urgency: {state.get('urgency') or state.get('ai_urgency') or '—'}\n"
        f"Score: {state.get('score') or '—'}\n"
        f"Summary: {state.get('ai_summary') or '—'}\n"
        f"Session: {state.get('session_id') or '—'}"
    )

    try:
        api = _client()
        from hubspot.crm.objects.meetings import SimplePublicObjectInputForCreate as MeetingCreate

        result = await asyncio.to_thread(
            api.crm.objects.meetings.basic_api.create,
            simple_public_object_input_for_create=MeetingCreate(
                properties={
                    "hs_meeting_title":          title,
                    "hs_meeting_body":           body,
                    "hs_meeting_start_time":     str(start_ms),
                    "hs_meeting_end_time":       str(end_ms),
                    "hs_meeting_outcome":        "SCHEDULED",
                    "hs_internal_meeting_notes": f"Automedge — score={state.get('score')}",
                }
            ),
        )
        meeting_id = result.id

        # Associate meeting → contact (v4 default)
        await asyncio.to_thread(
            api.crm.associations.v4.basic_api.create_default,
            object_type="meetings",
            object_id=meeting_id,
            to_object_type="contacts",
            to_object_id=contact_id,
        )

        log.info("meeting_created", meeting_id=meeting_id, start_ms=start_ms)
        return meeting_id

    except Exception as exc:
        log.error("book_meeting_failed", error=str(exc))
        return None


def _parse_slot_to_ms(slot_str: str | None) -> int:
    """
    Parse "Friday, Mar 21 at 10:00 AM" → epoch milliseconds.
    Falls back to tomorrow 9am UTC on any parse failure.
    """
    if slot_str:
        try:
            clean = slot_str.split(", ", 1)[-1]
            year  = datetime.now(timezone.utc).year
            dt    = datetime.strptime(f"{clean} {year}", "%b %d at %I:%M %p %Y")
            return int(dt.replace(tzinfo=timezone.utc).timestamp() * 1000)
        except Exception:
            pass

    tomorrow = (
        datetime.now(timezone.utc)
        .replace(hour=9, minute=0, second=0, microsecond=0)
        + timedelta(days=1)
    )
    return int(tomorrow.timestamp() * 1000)


# ── 5. Full pipeline ──────────────────────────────────────────────────────────

async def sync_lead_to_hubspot(state: dict) -> dict:
    """
    Full HubSpot sync after a session completes:
      1. Upsert contact
      2. Create deal (linked to contact)
      3. Book meeting (only if appointment was confirmed)

    Steps 2 and 3 are skipped if step 1 fails (no contact = nothing to link to).
    Each step is individually try/except'd in the caller — this function raises
    on unexpected errors so the caller can log appropriately.
    """
    log = logger.bind(service="sync_lead_to_hubspot",
                      session_id=state.get("session_id"))

    results: dict = {"contact_id": None, "deal_id": None, "meeting_id": None}

    contact_id = await upsert_contact(state)
    results["contact_id"] = contact_id

    if not contact_id:
        log.warning("hubspot_sync_aborted_no_contact")
        return results

    deal_id = await create_deal(state, contact_id)
    results["deal_id"] = deal_id

    if state.get("appt_booked") or state.get("appt_confirmed"):
        slot = state.get("appt_confirmed") or (
            state.get("appt_slots", [None])[0] if state.get("appt_slots") else None
        )
        results["meeting_id"] = await book_meeting(state, contact_id, slot)

    log.info("hubspot_sync_complete", **results)
    return results


# ── Module-level accessor ─────────────────────────────────────────────────────

class HubSpotTools:
    """Thin namespace wrapper for consistent import style across tools/."""
    upsert_contact = staticmethod(upsert_contact)
    update_contact = staticmethod(update_contact)
    update_deal    = staticmethod(update_deal)
    create_deal    = staticmethod(create_deal)
    book_meeting   = staticmethod(book_meeting)
    sync_lead      = staticmethod(sync_lead_to_hubspot)


hubspot_tools = HubSpotTools()