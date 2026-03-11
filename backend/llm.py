import logging
from dataclasses import dataclass
from typing import List

from groq import Groq
from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage

from core.config import settings

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Response wrapper
# ─────────────────────────────────────────────────────────────

@dataclass
class LLMResponse:
    content: str


# ─────────────────────────────────────────────────────────────
# Convert LangChain → OpenAI format
# ─────────────────────────────────────────────────────────────

def _to_openai_messages(messages: List[BaseMessage]) -> List[dict]:
    role_map = {
        "system": "system",
        "human": "user",
        "ai": "assistant",
        "assistant": "assistant",
    }

    formatted = []

    for m in messages:
        msg_type = m.__class__.__name__.lower().replace("message", "")
        role = role_map.get(msg_type, "user")

        formatted.append({
            "role": role,
            "content": m.content
        })

    return formatted


# ─────────────────────────────────────────────────────────────
# LLM Router
# ─────────────────────────────────────────────────────────────

class LLM:

    def __init__(self):

        self.use_groq = bool(settings.GROQ_API_KEY)
        self.env = settings.ENVIRONMENT.lower()

        # create clients ONCE (important optimization)
        if self.use_groq:
            self.groq = Groq(api_key=settings.GROQ_API_KEY)
            logger.info("LLM provider: Groq")
        else:
            self.groq = None

        self.ollama = ChatOllama(
            model="qwen3:1.7b",
            temperature=0.7,
        )

        if not self.use_groq:
            logger.info("LLM provider: Ollama")

    # ─────────────────────────────────────────

    def _call_groq(
        self,
        messages,
        max_tokens,
        temperature
    ) -> LLMResponse:

        response = self.groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        content = response.choices[0].message.content or ""

        return LLMResponse(content=content)

    # ─────────────────────────────────────────

    def _call_ollama(
        self,
        messages: List[BaseMessage]
    ) -> LLMResponse:

        response = self.ollama.invoke(messages)

        content = response.content if response else ""

        logger.debug(f"Ollama response → {len(content)} chars")

        return LLMResponse(content=content)

    # ─────────────────────────────────────────
    # Main invoke
    # ─────────────────────────────────────────

    def invoke(
        self,
        messages: List[BaseMessage],
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> LLMResponse:

        try:

            # Dev mode → always local model
            if self.env == "dev":
                return self._call_ollama(messages)

            # Production → Groq if configured
            if self.use_groq:
                openai_messages = _to_openai_messages(messages)

                return self._call_groq(
                    openai_messages,
                    max_tokens,
                    temperature,
                )

            # fallback if Groq key missing
            return self._call_ollama(messages)

        except Exception as e:

            logger.error(f"LLM error → fallback to Ollama: {e}")

            return self._call_ollama(messages)


# ─────────────────────────────────────────────────────────────
# Global instance
# ─────────────────────────────────────────────────────────────

llm = LLM()