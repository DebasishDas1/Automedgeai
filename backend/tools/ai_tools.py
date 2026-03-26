# services/ai_tools.py
from __future__ import annotations

import structlog
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage

from llm import llm
from workflows.base import full_transcript, parse_json
from workflows.hvac.schema import LeadEnrichment, LeadScore

logger = structlog.get_logger(__name__)

# ── Extraction prompt ─────────────────────────────────────────────────────────
# Key fixes:
# - "issue" now catches service-type phrases ("Priority Service", "AC Performance")
#   not just described problems
# - "address" catches city/state/zip — was being stored as "location" before
# - "urgency" catches intent signals ("priority", "urgent", "emergency", "ASAP")
#   not just explicit urgency words

_EXTRACT_SYSTEM = """\
Extract HVAC/home service lead fields from the user message. Return ONLY JSON.

{
  "name": str | null,
  "email": str | null,
  "phone": str | null,
  "issue": str | null,
  "description": str | null,
  "address": str | null,
  "urgency": "emergency" | "high" | "normal" | "low" | null,
  "is_homeowner": true | false | null
}

Field rules:
- issue: service category OR problem (e.g. "AC Performance", "Priority Service",
  "no heat", "burst pipe"). Catch broad service-type phrases as issue.
- description: specific symptom detail beyond the category.
- address: ANY location mention — city, state, zip, street address.
  "Austin TX", "Austin, Texas", "78701", "123 Main St" all map to address.
  NEVER leave address null if any location is mentioned.
- urgency: infer from language signals —
    emergency = "emergency", "no heat", "flooding", "gas smell", "right now"
    high      = "priority", "urgent", "ASAP", "very urgent", "need help today"
    normal    = "need service", "not working", general requests
    low       = "quote", "estimate", "planning", "sometime"
  null ONLY if message contains no urgency signal at all.
- phone: digits only, strip formatting.
- email: lowercase.
- is_homeowner: true if "my house/home/property", false if "rental/renting".
- null for anything not present or inferable.
"""

_CLASSIFY_SYSTEM = """\
Classify home service conversation. Return ONLY JSON.

{
  "urgency": "emergency" | "high" | "normal" | "low",
  "intent": "information" | "service_request" | "complaint" | "spam",
  "is_spam": bool,
  "summary": str
}

urgency: emergency=safety/system down, high=not working/priority,
         normal=degraded/routine, low=planning/quotes.
summary: 1 professional CRM sentence covering issue, location, urgency.
"""

_SCORE_SYSTEM = """\
Score home service lead. Return ONLY JSON.

{
  "score": "hot" | "warm" | "cold",
  "score_reason": str,
  "next_step": "immediate_dispatch" | "schedule_callback" | "nurture" | "drop"
}

hot=urgent+contact info, warm=interested+incomplete, cold=browsing, drop=spam.
"""


class AITools:

    async def extract_fields(self, last_user_message: str) -> dict | None:
        log = logger.bind(service="extract_fields")
        try:
            resp = await llm.ainvoke([
                SystemMessage(content=_EXTRACT_SYSTEM),
                HumanMessage(content=last_user_message),
            ])
            data = parse_json(resp.content)
            if data:
                log.debug("extract_fields_ok", fields={
                    k: v for k, v in data.items() if v is not None})
                return data
            log.warning("extract_fields_empty", raw=resp.content[:120])
            return None
        except Exception as exc:
            log.error("extract_fields_failed", error=str(exc))
            return None


    async def extract_pest_fields(self, last_user_message: str) -> dict | None:
        """
        Extract pest-control-specific fields from a single user message.
        Separate from extract_fields() so pest and HVAC schemas stay independent.
        """
        from workflows.pest_control.prompts import PEST_EXTRACT_SYSTEM
        log = logger.bind(service="extract_pest_fields")
        try:
            resp = await llm.ainvoke([
                SystemMessage(content=PEST_EXTRACT_SYSTEM),
                HumanMessage(content=last_user_message),
            ])
            data = parse_json(resp.content)
            if data:
                # Filter out all-null dicts to avoid noisy logging
                non_null = {k: v for k, v in data.items() if v is not None}
                log.debug("extract_pest_fields_ok", fields=non_null)
                return data
            log.warning("extract_pest_fields_empty", raw=resp.content[:120])
            return None
        except Exception as exc:
            log.error("extract_pest_fields_failed", error=str(exc))
            return None


    async def extract_plumbing_fields(self, last_user_message: str) -> dict | None:
        """
        Extract plumbing-specific fields from a single user message.
        Handles emergency vs routine detection, water damage signals,
        and shutoff valve status.
        """
        from workflows.plumbing.prompts import PLUMBING_EXTRACT_SYSTEM
        log = logger.bind(service="extract_plumbing_fields")
        try:
            resp = await llm.ainvoke([
                SystemMessage(content=PLUMBING_EXTRACT_SYSTEM),
                HumanMessage(content=last_user_message),
            ])
            data = parse_json(resp.content)
            if data:
                non_null = {k: v for k, v in data.items() if v is not None}
                log.debug("extract_plumbing_fields_ok", fields=non_null)
                return data
            log.warning("extract_plumbing_fields_empty", raw=resp.content[:120])
            return None
        except Exception as exc:
            log.error("extract_plumbing_fields_failed", error=str(exc))
            return None


    async def extract_roofing_fields(self, last_user_message: str) -> dict | None:
        """
        Extract roofing-specific fields from a single user message.
        Handles storm vs wear detection, insurance status, and adjuster involvement.
        """
        from workflows.roofing.prompts import ROOFING_EXTRACT_SYSTEM
        log = logger.bind(service="extract_roofing_fields")
        try:
            resp = await llm.ainvoke([
                SystemMessage(content=ROOFING_EXTRACT_SYSTEM),
                HumanMessage(content=last_user_message),
            ])
            data = parse_json(resp.content)
            if data:
                non_null = {k: v for k, v in data.items() if v is not None}
                log.debug("extract_roofing_fields_ok", fields=non_null)
                return data
            log.warning("extract_roofing_fields_empty", raw=resp.content[:120])
            return None
        except Exception as exc:
            log.error("extract_roofing_fields_failed", error=str(exc))
            return None


    async def classify_conversation(self, messages: list[dict]) -> dict | None:
        log = logger.bind(service="classify_conversation")
        transcript = full_transcript({"messages": messages})
        if not transcript.strip():
            return None
        try:
            resp = await llm.ainvoke(
                [SystemMessage(content=_CLASSIFY_SYSTEM),
                 HumanMessage(content=transcript)],
                full_history=True,
            )
            data = parse_json(resp.content)
            if data:
                log.debug("classify_ok", urgency=data.get("urgency"),
                          is_spam=data.get("is_spam"))
                return data
            log.warning("classify_empty", raw=resp.content[:120])
            return None
        except Exception as exc:
            log.error("classify_failed", error=str(exc))
            return None

    async def score_lead(self, enrichment: LeadEnrichment) -> LeadScore:
        log = logger.bind(service="score_lead")

        if enrichment.is_spam:
            return LeadScore(score="cold",
                score_reason="Spam or bot.", next_step="drop")
        if enrichment.urgency in ("emergency", "high"):
            return LeadScore(score="hot",
                score_reason="Active emergency.", next_step="immediate_dispatch")

        lead_ctx = (
            f"Issue: {enrichment.issue or 'unknown'}\n"
            f"Urgency: {enrichment.urgency}\n"
            f"Intent: {enrichment.intent}\n"
            f"Has name: {enrichment.name is not None}\n"
            f"Has phone: {enrichment.phone is not None}\n"
            f"Has email: {enrichment.email is not None}"
        )
        try:
            resp = await llm.ainvoke([
                SystemMessage(content=_SCORE_SYSTEM),
                HumanMessage(content=lead_ctx),
            ])
            data = parse_json(resp.content)
            if data:
                log.info("score_ok", score=data.get("score"),
                    next_step=data.get("next_step"))
                return LeadScore(
                    score=data.get("score", "warm"),
                    score_reason=data.get("score_reason", "LLM assessment."),
                    next_step=data.get("next_step", "schedule_callback"),
                )
        except Exception as exc:
            log.error("score_failed", error=str(exc))

        return LeadScore(score="warm",
            score_reason="Defaulted to warm.", next_step="schedule_callback")

    async def enrich_lead(self, messages: list[dict]) -> Optional[LeadEnrichment]:
        """Legacy single-pass for non-HVAC verticals."""
        log = logger.bind(service="enrich_lead_legacy")
        last_user = next(
            (m["content"] for m in reversed(messages) if m.get("role") == "user"), None)
        if not last_user:
            return None
        fields = await self.extract_fields(last_user)
        classification = await self.classify_conversation(messages)
        if not fields and not classification:
            return None
        merged = {**(fields or {}), **(classification or {})}
        try:
            return LeadEnrichment(**merged)
        except Exception as exc:
            log.error("enrich_model_failed", error=str(exc))
            return None


ai_tools = AITools()