# llm.py
import asyncio
import structlog
from typing import List, Any
from langchain_core.messages import BaseMessage, SystemMessage
from core.config import settings
from core.cache import cache

logger = structlog.get_logger(__name__)
_llm_semaphore = asyncio.Semaphore(20)


class LLMManager:
    def __init__(self):
        self._groq = None
        self._ollama = None

        if settings.GROQ_API_KEY:
            from langchain_groq import ChatGroq
            self._groq = ChatGroq(
                api_key=settings.GROQ_API_KEY,
                model="llama-3.3-70b-versatile",
                temperature=0.3,
                timeout=15.0,
            )

        from langchain_ollama import ChatOllama
        self._ollama = ChatOllama(
            model=settings.OLLAMA_MODEL or "llama3.1:8b",
            temperature=0.1,
        )

    def _select(self):
        return self._groq if self._groq else self._ollama

    async def ainvoke(
        self,
        messages: List[BaseMessage],
        session_id: str = "global",
        full_history: bool = False,
        use_cache: bool = False,   # FIX: explicitly opt-in. Chat replies must NOT be cached.
        **kwargs,
    ) -> Any:
        system_msg = next((m for m in messages if isinstance(m, SystemMessage)), None)
        other_msgs = [m for m in messages if not isinstance(m, SystemMessage)]

        if full_history:
            # Classification needs every turn — never trim
            trimmed = ([system_msg] if system_msg else []) + other_msgs
        else:
            # Chat reply: keep last 6 turns to control token usage
            trimmed = ([system_msg] if system_msg else []) + other_msgs[-6:]

        logger.debug("llm_request",
            model=type(self._select()).__name__,
            msg_count=len(trimmed),
            session_id=session_id,
            full_history=full_history,
            last_user=(other_msgs[-1].content[:60] if other_msgs else ""),
        )

        # FIX: cache key MUST include session context to prevent data leakage 
        # across users in a shared process cache.
        key = [(type(m).__name__, m.content) for m in trimmed]
        key.append(("session_id", session_id))

        if use_cache and settings.ENVIRONMENT != "dev":
            cached = await cache.get("llm", key)
            if cached:
                return cached

        async with _llm_semaphore:
            target = self._select()
            try:
                resp = await self._call(target, trimmed, **kwargs)
                if use_cache and settings.ENVIRONMENT != "dev":
                    await cache.set("llm", key, resp, ttl=1800)
                return resp
            except Exception as exc:
                logger.error(
                    "llm_primary_failed",
                    error_type=type(exc).__name__,
                )
                if target is not self._ollama:
                    logger.warning("llm_fallback_to_ollama")
                    return await self._call(self._ollama, trimmed, **kwargs)
                raise

    async def _call(self, model, msgs, **kwargs):
        return await asyncio.wait_for(model.ainvoke(msgs, **kwargs), timeout=15.0)


llm = LLMManager()