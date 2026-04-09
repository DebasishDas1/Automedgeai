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


def _client(app_state=None):
    """
    Get HubSpot client from app_state context (best for performance) 
    or fall back to the module-level singleton.
    """
    global _hs_client
    
    if app_state and hasattr(app_state, "hubspot") and app_state.hubspot:
        return app_state.hubspot
        
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
    """Normalize phone to E.164 digits only using phonenumbers library."""
    if not phone:
        return None
    try:
        import phonenumbers
        # Try US as default, then fallback to current E.164 if already formatted
        parsed = phonenumbers.parse(phone, "US")
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        pass
        
    # Fallback to digits only if phonenumbers fails
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
        "hot":  settings.HUBSPOT_STAGE_HOT,
        "warm": settings.HUBSPOT_STAGE_WARM,
        "cold": settings.HUBSPOT_STAGE_COLD,
    }
    return stage_map.get(score or "warm", stage_map["warm"])


def _pipeline_id() -> str:
    return settings.HUBSPOT_PIPELINE_ID


def _issue_field(state: dict) -> str:
    """Resolve the issue field across all verticals."""
    return (
        state.get("issue")
        or state.get("pest_type")
        or state.get("damage_type")
        or ""
    )


def _build_contact_properties(state: dict) -> dict:
    """
    Build a clean HubSpot v3 contact properties object.
    
    Validation rules:
    - firstname and email are required
    - Remove all empty/None/undefined values
    - Phone must be in E.164 format or omitted
    - All keys must be valid HubSpot contact properties
    
    Returns: dict with only non-empty properties
    Raises: ValueError if required fields are missing
    """
    email = state.get("email", "").strip()
    name = (state.get("name") or "").strip()
    phone = state.get("phone")
    
    # Validate required fields
    if not email:
        raise ValueError("email is required for HubSpot contact")
    if not name:
        raise ValueError("name is required for HubSpot contact")
    
    parts = name.split(" ", 1)
    first = parts[0].strip()
    last = parts[1].strip() if len(parts) > 1 else ""
    
    if not first:
        raise ValueError("firstname must be non-empty")
    
    # Build properties — only include non-empty values
    props = {
        "firstname": first,
        "email": email,
        "hs_lead_status": "NEW",
    }
    
    if last:
        props["lastname"] = last
    
    phone_clean = _phone_clean(phone)
    if phone_clean:
        props["phone"] = phone_clean
    
    address = state.get("address", "").strip()
    if address:
        props["address"] = address
    
    vertical = state.get("vertical", "").strip()
    if vertical:
        props["vertical"] = vertical
    
    issue = _issue_field(state).strip()
    if issue:
        props["issue"] = issue
    
    urgency = (state.get("urgency") or state.get("ai_urgency", "")).strip()
    if urgency:
        props["urgency"] = urgency
    
    score = state.get("score", "").strip()
    if score:
        props["score"] = score
    
    summary = state.get("ai_summary", "").strip()
    if summary:
        props["summary"] = summary
    
    session_id = state.get("session_id", "").strip()
    if session_id:
        props["session_id"] = session_id
    
    return props


# ── 1. Upsert contact ─────────────────────────────────────────────────────────

async def upsert_contact(state: dict, app_state=None) -> Optional[str]:
    """
    Create or update a HubSpot contact by email.
    Returns the HubSpot contact ID, or None on failure.

    Custom contact properties required in HubSpot (Settings → Properties → Contact):
        vertical, issue, urgency, score, summary, session_id
    
    Validates payload before sending to ensure compliance with HubSpot v3 API.
    """
    log = logger.bind(service="hubspot_upsert_contact",
                      session_id=state.get("session_id"))

    # Validate and build clean properties dict
    try:
        props = _build_contact_properties(state)
    except ValueError as e:
        log.error(
            "contact_validation_failed",
            error_type=type(e).__name__,
            detail=str(e),
        )
        return None

    email = state.get("email", "").strip()

    try:
        api = _client(app_state)

        # Try update-by-email first to avoid duplicates
        if email:
            try:
                from hubspot.crm.contacts import PublicObjectSearchRequest, FilterGroup, Filter
                search_resp = await asyncio.to_thread(
                    api.crm.contacts.search_api.do_search,
                    public_object_search_request=PublicObjectSearchRequest(
                        filter_groups=[FilterGroup(
                            filters=[Filter(
                                property_name="email",
                                operator="EQ",
                                value=email,
                            )]
                        )],
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
                    log.info("contact_updated", contact_id=contact_id, fields=list(props.keys()))
                    return contact_id
            except Exception as exc:
                # Log and fall through to create — don't swallow silently
                error_detail = ""
                if hasattr(exc, "body"):
                    try:
                        import json
                        error_body = json.loads(exc.body) if isinstance(exc.body, str) else exc.body
                        error_detail = error_body.get("message") or str(error_body)
                    except Exception:
                        error_detail = str(exc.body)[:200]
                
                log.warning(
                    "contact_search_failed_falling_through_to_create",
                    error_type=type(exc).__name__,
                    error_detail=error_detail[:200] if error_detail else None,
                )

        # Create new contact
        from hubspot.crm.contacts import SimplePublicObjectInputForCreate
        result = await asyncio.to_thread(
            api.crm.contacts.basic_api.create,
            simple_public_object_input_for_create=SimplePublicObjectInputForCreate(
                properties=props
            ),
        )
        contact_id = result.id
        log.info("contact_created", contact_id=contact_id, fields=list(props.keys()))
        return contact_id

    except Exception as exc:
        error_detail = ""
        if hasattr(exc, "body"):
            try:
                import json
                error_body = json.loads(exc.body) if isinstance(exc.body, str) else exc.body
                error_detail = error_body.get("message") or str(error_body)
            except Exception:
                error_detail = str(exc.body)[:200]
        
        log.error(
            "upsert_contact_failed",
            error_type=type(exc).__name__,
            error_detail=error_detail[:200] if error_detail else None,
        )
        return None


# ── 2. Create deal ────────────────────────────────────────────────────────────

async def create_deal(state: dict, contact_id: str, app_state=None) -> Optional[str]:
    """
    Create a HubSpot deal and associate it with the contact.
    Returns the deal ID, or None on failure.

    Custom deal properties required in HubSpot (Settings → Properties → Deal):
        automedge_score
    
    Optional deal properties may be configured via the env vars:
        HUBSPOT_DEAL_SCORE_PROPERTY
        HUBSPOT_DEAL_VERTICAL_PROPERTY

    Note: dealname, pipeline, dealstage are optional in HubSpot v3.
    Only include valid values to avoid API validation errors.
    """
    log = logger.bind(service="hubspot_create_deal",
                      session_id=state.get("session_id"))

    vertical = state.get("vertical", "hvac").replace("_", " ").title()
    issue = _issue_field(state) or "Service Request"
    score = state.get("score") or "warm"
    name = state.get("name") or "Lead"
    address = state.get("address", "").strip()

    deal_name = f"{vertical} — {issue} ({name})"
    if address:
        deal_name += f" — {address}"

    # Build clean properties dict — only include valid, non-empty values
    # dealname, pipeline, dealstage are optional in HubSpot v3
    props = {}
    
    if deal_name:
        props["dealname"] = deal_name
    
    # Only include dealstage if score is valid
    if score:
        stage = _score_to_hs_stage(score)
        if stage and stage != "default":
            props["dealstage"] = stage
    
    # Only include pipeline if it's a valid ID (not "default" string)
    pipeline = _pipeline_id()
    if pipeline and pipeline != "default" and pipeline.strip():
        props["pipeline"] = pipeline
    
    summary = state.get("ai_summary", "").strip()
    if summary:
        props["description"] = summary
    
    score_property = settings.HUBSPOT_DEAL_SCORE_PROPERTY
    if score_property and score:
        props[score_property] = score

    vertical_property = settings.HUBSPOT_DEAL_VERTICAL_PROPERTY
    vert = state.get("vertical", "").strip()
    if vertical_property and vert:
        props[vertical_property] = vert

    # Insurance roofing leads get a conservative deal value for pipeline weighting
    if state.get("vertical") == "roofing" and state.get("has_insurance"):
        props["amount"] = "15000"

    try:
        api = _client(app_state)
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
            "deals",
            deal_id,
            "contacts",
            contact_id,
        )

        log.info("deal_created", deal_id=deal_id, score=score, fields=list(props.keys()))
        return deal_id

    except Exception as exc:
        # Try to extract HubSpot API error details
        error_detail = ""
        if hasattr(exc, "body"):
            try:
                import json
                error_body = json.loads(exc.body) if isinstance(exc.body, str) else exc.body
                error_detail = error_body.get("message") or str(error_body)
            except Exception:
                error_detail = str(exc.body)[:200]

        if not error_detail:
            error_detail = str(exc)[:200]
        
        log.error(
            "create_deal_failed",
            error_type=type(exc).__name__,
            error_detail=error_detail[:200] if error_detail else None,
        )
        return None


# ── 3. Update contact / deal ──────────────────────────────────────────────────

async def update_contact(contact_id: str, updates: dict, app_state=None) -> bool:
    """Update arbitrary properties on an existing HubSpot contact."""
    log = logger.bind(service="hubspot_update_contact", contact_id=contact_id)
    try:
        from hubspot.crm.contacts import SimplePublicObjectInput
        api = _client(app_state)
        await asyncio.to_thread(
            api.crm.contacts.basic_api.update,
            contact_id=contact_id,
            simple_public_object_input=SimplePublicObjectInput(properties=updates),
        )
        log.info("contact_props_updated", fields=list(updates.keys()))
        return True
    except Exception as exc:
        error_detail = ""
        if hasattr(exc, "body"):
            try:
                import json
                error_body = json.loads(exc.body) if isinstance(exc.body, str) else exc.body
                error_detail = error_body.get("message") or str(error_body)
            except Exception:
                error_detail = str(exc.body)[:200]
        
        log.error(
            "update_contact_failed",
            error_type=type(exc).__name__,
            error_detail=error_detail[:200] if error_detail else None,
        )
        return False


async def update_deal(deal_id: str, updates: dict, app_state=None) -> bool:
    """Update arbitrary properties on an existing HubSpot deal."""
    log = logger.bind(service="hubspot_update_deal", deal_id=deal_id)
    try:
        from hubspot.crm.deals import SimplePublicObjectInput
        api = _client(app_state)
        await asyncio.to_thread(
            api.crm.deals.basic_api.update,
            deal_id=deal_id,
            simple_public_object_input=SimplePublicObjectInput(properties=updates),
        )
        log.info("deal_props_updated", fields=list(updates.keys()))
        return True
    except Exception as exc:
        error_detail = ""
        if hasattr(exc, "body"):
            try:
                import json
                error_body = json.loads(exc.body) if isinstance(exc.body, str) else exc.body
                error_detail = error_body.get("message") or str(error_body)
            except Exception:
                error_detail = str(exc.body)[:200]
        
        log.error(
            "update_deal_failed",
            error_type=type(exc).__name__,
            error_detail=error_detail[:200] if error_detail else None,
        )
        return False


# ── 4. Book meeting ───────────────────────────────────────────────────────────

async def book_meeting(
    state: dict,
    contact_id: str,
    slot_str: str | None = None,
    app_state=None,
) -> Optional[str]:
    """
    Create a HubSpot meeting engagement and link it to the contact.
    Returns the meeting ID, or None on failure.
    
    Validates meeting properties before sending to HubSpot v3 API.
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
    address  = state.get("address", "").strip()

    title = f"{vertical} Inspection — {name}"
    if address:
        title += f" @ {address}"

    # Build clean meeting properties
    props = {
        "hs_meeting_title": title,
        "hs_meeting_start_time": str(start_ms),
        "hs_meeting_end_time": str(end_ms),
        "hs_meeting_outcome": "SCHEDULED",
    }
    
    body = (
        f"Vertical: {vertical}\n"
        f"Issue: {issue}\n"
    )
    if address:
        body += f"Address: {address}\n"
    
    urgency = state.get("urgency") or state.get("ai_urgency", "").strip()
    if urgency:
        body += f"Urgency: {urgency}\n"
    
    score = state.get("score", "").strip()
    if score:
        body += f"Score: {score}\n"
    
    summary = state.get("ai_summary", "").strip()
    if summary:
        body += f"Summary: {summary}\n"
    
    session_id = state.get("session_id", "").strip()
    if session_id:
        body += f"Session: {session_id}\n"
    
    if body:
        props["hs_meeting_body"] = body.rstrip()
    
    if score:
        props["hs_internal_meeting_notes"] = f"Automedge — score={score}"

    try:
        api = _client(app_state)
        from hubspot.crm.objects.meetings import SimplePublicObjectInputForCreate as MeetingCreate

        result = await asyncio.to_thread(
            api.crm.objects.meetings.basic_api.create,
            simple_public_object_input_for_create=MeetingCreate(
                properties=props
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

        log.info("meeting_created", meeting_id=meeting_id, start_ms=start_ms, fields=list(props.keys()))
        return meeting_id

    except Exception as exc:
        error_detail = ""
        if hasattr(exc, "body"):
            try:
                import json
                error_body = json.loads(exc.body) if isinstance(exc.body, str) else exc.body
                error_detail = error_body.get("message") or str(error_body)
            except Exception:
                error_detail = str(exc.body)[:200]
        
        log.error(
            "book_meeting_failed",
            error_type=type(exc).__name__,
            error_detail=error_detail[:200] if error_detail else None,
        )
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

async def sync_lead_to_hubspot(state: dict, app_state=None) -> dict:
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

    contact_id = await upsert_contact(state, app_state=app_state)
    results["contact_id"] = contact_id

    if not contact_id:
        log.warning("hubspot_sync_aborted_no_contact")
        return results

    deal_id = await create_deal(state, contact_id, app_state=app_state)
    results["deal_id"] = deal_id

    if state.get("appt_booked") or state.get("appt_confirmed"):
        slot = state.get("appt_confirmed") or (
            state.get("appt_slots", [None])[0] if state.get("appt_slots") else None
        )
        results["meeting_id"] = await book_meeting(state, contact_id, slot, app_state=app_state)

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