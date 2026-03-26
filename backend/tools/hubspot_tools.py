# services/hubspot_tools.py
# HubSpot CRM integration — contacts, deals, and meetings.
# Requires: uv add hubspot-api-client
# Env vars: HUBSPOT_ACCESS_TOKEN (private app token from HubSpot settings)
from __future__ import annotations

import asyncio
import structlog
from datetime import datetime, timezone
from typing import Optional
from core.config import settings

logger = structlog.get_logger(__name__)


def _client():
    try:
        from hubspot import HubSpot
    except ImportError:
        raise RuntimeError("Run: uv add hubspot-api-client")
    token = settings.HUBSPOT_ACCESS_TOKEN
    if not token:
        raise RuntimeError("HUBSPOT_ACCESS_TOKEN env var not set")
    return HubSpot(access_token=token)


def _phone_clean(phone: str | None) -> str | None:
    """Normalize phone to E.164-ish digits only."""
    if not phone:
        return None
    digits = "".join(c for c in phone if c.isdigit())
    return f"+{digits}" if digits else None


def _score_to_hs_stage(score: str | None) -> str:
    """Map internal score to HubSpot deal pipeline stage label."""
    return {
        "hot":  "appointmentscheduled",
        "warm": "qualifiedtobuy",
        "cold": "presentationscheduled",
    }.get(score or "warm", "qualifiedtobuy")


# ── 1. Create or update contact ───────────────────────────────────────────────

async def upsert_contact(state: dict) -> Optional[str]:
    """
    Create a new HubSpot contact, or update if email already exists.
    Returns the HubSpot contact ID on success, None on failure.
    """
    log = logger.bind(service="hubspot_upsert_contact")

    email = state.get("email")
    name  = state.get("name") or ""
    parts = name.strip().split(" ", 1)
    first = parts[0]
    last  = parts[1] if len(parts) > 1 else ""

    props = {
        "firstname":   first,
        "lastname":    last,
        "phone":       _phone_clean(state.get("phone")) or "",
        "address":     state.get("address") or "",
        # Custom properties — add these in HubSpot settings → Properties
        "hs_lead_status":       "NEW",
        "automedge_vertical":   state.get("vertical", "hvac"),
        "automedge_issue":      state.get("issue") or state.get("pest_type") or
                                state.get("damage_type") or "",
        "automedge_urgency":    state.get("urgency") or state.get("ai_urgency") or "",
        "automedge_score":      state.get("score") or "",
        "automedge_summary":    state.get("ai_summary") or "",
        "automedge_session_id": state.get("session_id") or "",
    }
    if email:
        props["email"] = email

    try:
        api = _client()

        if email:
            # Try to find existing contact by email first
            try:
                from hubspot.crm.contacts import SimplePublicObjectInputForCreate
                search_resp = await asyncio.to_thread(
                    api.crm.contacts.search_api.do_search,
                    public_object_search_request={
                        "filterGroups": [{
                            "filters": [{
                                "propertyName": "email",
                                "operator": "EQ",
                                "value": email,
                            }]
                        }],
                        "properties": ["id"],
                        "limit": 1,
                    }
                )
                if search_resp.results:
                    contact_id = search_resp.results[0].id
                    # Update existing contact
                    await asyncio.to_thread(
                        api.crm.contacts.basic_api.update,
                        contact_id=contact_id,
                        simple_public_object_input={"properties": props},
                    )
                    log.info("contact_updated", contact_id=contact_id)
                    return contact_id
            except Exception:
                pass  # Fall through to create

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


# ── 2. Create deal (lead record) ──────────────────────────────────────────────

async def create_deal(state: dict, contact_id: str) -> Optional[str]:
    """
    Create a HubSpot deal linked to the contact.
    Returns the deal ID on success, None on failure.
    """
    log = logger.bind(service="hubspot_create_deal")

    vertical  = state.get("vertical", "hvac").replace("_", " ").title()
    issue     = (state.get("issue") or state.get("pest_type") or
                 state.get("damage_type") or "Service Request")
    score     = state.get("score") or "warm"
    name      = state.get("name") or "Lead"
    address   = state.get("address") or ""

    deal_name = f"{vertical} — {issue} ({name})"
    if address:
        deal_name += f" — {address}"

    props = {
        "dealname":   deal_name,
        "dealstage":  _score_to_hs_stage(score),
        "pipeline":   "default",
        "description": state.get("ai_summary") or "",
        "automedge_score":    score,
        "automedge_vertical": state.get("vertical", "hvac"),
    }

    # Amount hint for high-value roofing insurance leads
    if state.get("vertical") == "roofing" and state.get("has_insurance"):
        props["amount"] = "15000"  # conservative storm replacement estimate

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

        # Associate deal → contact
        await asyncio.to_thread(
            api.crm.deals.associations_api.create,
            deal_id=deal_id,
            to_object_type="contacts",
            to_object_id=contact_id,
            association_type="deal_to_contact",
        )

        log.info("deal_created", deal_id=deal_id, score=score)
        return deal_id

    except Exception as exc:
        log.error("create_deal_failed", error=str(exc))
        return None


# ── 3. Update existing contact/deal ──────────────────────────────────────────

async def update_contact(contact_id: str, updates: dict) -> bool:
    """
    Update arbitrary properties on an existing HubSpot contact.
    Pass a flat dict of HubSpot property names → values.

    Example:
        await hubspot_tools.update_contact(contact_id, {
            "hs_lead_status": "IN_PROGRESS",
            "automedge_score": "hot",
        })
    """
    log = logger.bind(service="hubspot_update_contact", contact_id=contact_id)
    try:
        api = _client()
        await asyncio.to_thread(
            api.crm.contacts.basic_api.update,
            contact_id=contact_id,
            simple_public_object_input={"properties": updates},
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
        api = _client()
        await asyncio.to_thread(
            api.crm.deals.basic_api.update,
            deal_id=deal_id,
            simple_public_object_input={"properties": updates},
        )
        log.info("deal_props_updated", fields=list(updates.keys()))
        return True
    except Exception as exc:
        log.error("update_deal_failed", error=str(exc))
        return False


# ── 4. Book appointment (HubSpot meeting) ─────────────────────────────────────

async def book_meeting(
    state: dict,
    contact_id: str,
    slot_str: str | None = None,
) -> Optional[str]:
    """
    Create a HubSpot meeting (engagement) and link it to the contact.

    slot_str: human-readable slot like "Friday, Mar 21 at 10:00 AM".
              Falls back to first appt_slot in state, then current time + 1 day.
    Returns the meeting engagement ID on success, None on failure.
    """
    log = logger.bind(service="hubspot_book_meeting")

    # Resolve slot → epoch milliseconds
    slot = slot_str or (
        state.get("appt_slots", [None])[0]
        if state.get("appt_slots") else None
    )

    start_ms = _parse_slot_to_ms(slot)
    end_ms   = start_ms + 3_600_000  # 1-hour meeting by default

    vertical = state.get("vertical", "hvac").replace("_", " ").title()
    issue    = (state.get("issue") or state.get("pest_type") or
                state.get("damage_type") or "service request")
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

        # Create meeting engagement
        result = await asyncio.to_thread(
            api.crm.objects.meetings.basic_api.create,
            simple_public_object_input_for_create={
                "properties": {
                    "hs_meeting_title":          title,
                    "hs_meeting_body":           body,
                    "hs_meeting_start_time":     str(start_ms),
                    "hs_meeting_end_time":       str(end_ms),
                    "hs_meeting_outcome":        "SCHEDULED",
                    "hs_internal_meeting_notes": f"Automedge lead — score={state.get('score')}",
                }
            }
        )
        meeting_id = result.id

        # Associate meeting → contact
        await asyncio.to_thread(
            api.crm.objects.meetings.associations_api.create,
            meeting_id=meeting_id,
            to_object_type="contacts",
            to_object_id=contact_id,
            association_type="meeting_to_contact",
        )

        log.info("meeting_created", meeting_id=meeting_id, start_ms=start_ms)
        return meeting_id

    except Exception as exc:
        log.error("book_meeting_failed", error=str(exc))
        return None


def _parse_slot_to_ms(slot_str: str | None) -> int:
    """
    Parse a slot string like "Friday, Mar 21 at 10:00 AM" to epoch milliseconds.
    Falls back to tomorrow 9am UTC on any parse failure.
    """
    if slot_str:
        try:
            # Strip weekday prefix: "Friday, Mar 21 at 10:00 AM" → "Mar 21 at 10:00 AM"
            clean = slot_str.split(", ", 1)[-1]
            year  = datetime.now(timezone.utc).year
            dt    = datetime.strptime(f"{clean} {year}", "%b %d at %I:%M %p %Y")
            dt    = dt.replace(tzinfo=timezone.utc)
            return int(dt.timestamp() * 1000)
        except Exception:
            pass

    # Fallback: tomorrow 9am UTC
    from datetime import timedelta
    tomorrow = datetime.now(timezone.utc).replace(
        hour=9, minute=0, second=0, microsecond=0
    ) + timedelta(days=1)
    return int(tomorrow.timestamp() * 1000)


# ── 5. Full pipeline entry point ──────────────────────────────────────────────

async def sync_lead_to_hubspot(state: dict) -> dict:
    """
    Orchestrates the full HubSpot sync after a session completes:
      1. Upsert contact
      2. Create deal linked to contact
      3. Book meeting if appointment was confirmed

    Returns a results dict for logging. All steps are isolated —
    failure in one never blocks the others.
    """
    log = logger.bind(service="sync_lead_to_hubspot",
                      session_id=state.get("session_id"))

    results = {
        "contact_id": None,
        "deal_id":    None,
        "meeting_id": None,
    }

    # Step 1: contact
    contact_id = await upsert_contact(state)
    results["contact_id"] = contact_id

    if not contact_id:
        log.warning("hubspot_sync_aborted_no_contact")
        return results

    # Step 2: deal
    deal_id = await create_deal(state, contact_id)
    results["deal_id"] = deal_id

    # Step 3: meeting — only if appointment was confirmed
    if state.get("appt_booked") or state.get("appt_confirmed"):
        slot = state.get("appt_confirmed") or (
            state.get("appt_slots", [None])[0] if state.get("appt_slots") else None
        )
        meeting_id = await book_meeting(state, contact_id, slot)
        results["meeting_id"] = meeting_id

    log.info("hubspot_sync_complete", **results)
    return results


# Module-level singleton-style access
class HubSpotTools:
    """Thin wrapper so the service can be imported as hubspot_tools.method()."""
    upsert_contact  = staticmethod(upsert_contact)
    update_contact  = staticmethod(update_contact)
    update_deal     = staticmethod(update_deal)
    create_deal     = staticmethod(create_deal)
    book_meeting    = staticmethod(book_meeting)
    sync_lead       = staticmethod(sync_lead_to_hubspot)


hubspot_tools = HubSpotTools()