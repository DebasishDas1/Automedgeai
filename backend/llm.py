from langchain_openai import ChatOpenAI
from core.config import settings
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama

OpenAI_llm = ChatOpenAI(
        model="gpt-4", 
        openai_api_key=settings.OPENAI_API_KEY,
        temperature=0,
        max_tokens=3000,
        max_retries=2,
    )

Groq_llm = ChatGroq(
    model="llama-3.1-8b-instant",
    groq_api_key=settings.GROQ_API_KEY,
    temperature=0.4,
    max_tokens=settings.MAX_TOKEN,
    max_retries=3
)

Ollama_llm = ChatOllama(
        model="qwen3:1.7b", 
        temperature=0,
        max_tokens=3000,
    )

llm = Ollama_llm