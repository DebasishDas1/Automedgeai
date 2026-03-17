import asyncio
import structlog
from typing import List, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage
from core.config import settings
from core.cache import cache

logger = structlog.get_logger(__name__)

# Global concurrency guard for LLM calls (prevents event loop saturation)
_llm_semaphore = asyncio.Semaphore(20)

class LLMManager:
    def __init__(self):
        self._primary = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            timeout=10.0
        ) if settings.GROQ_API_KEY else None

        self._fallback = ChatOllama(
            model="qwen3:1.7b",
            temperature=0.7,
        )

    async def ainvoke(self, messages: List[BaseMessage], **kwargs) -> Any:
        # Context window management
        trimmed = messages[-8:]
        
        # Cache check
        key = str([m.content for m in trimmed])
        cached = cache.get("llm", key)
        if cached: return cached

        async with _llm_semaphore:
            try:
                use_groq = settings.ENVIRONMENT == "prod" and self._primary
                target = self._primary if use_groq else self._fallback
                resp = await self._call(target, trimmed, **kwargs)
                cache.set("llm", key, resp, ttl=1800)
                return resp
            except Exception as e:
                logger.error("llm_error", error=str(e))
                if target != self._fallback:
                    return await self._call(self._fallback, trimmed, **kwargs)
                raise

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
    async def _call(self, llm, msgs, **kwargs):
        return await asyncio.wait_for(llm.ainvoke(msgs, **kwargs), timeout=12.0)

llm = LLMManager()