"""Factory for instantiating the appropriate LLM provider."""
from __future__ import annotations

from app.core.config import logger, settings
from app.providers.base import BaseLLMProvider
from app.providers.claude_provider import ClaudeProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.mock_provider import MockProvider
from app.providers.ollama_provider import OllamaProvider
from app.providers.openai_provider import OpenAIProvider


def get_llm_provider(name: str | None = None) -> BaseLLMProvider:
    """Return configured provider or fallback to mock if credentials missing."""
    provider_name = (name or settings.default_llm_provider).lower()

    if provider_name == "claude":
        prov = ClaudeProvider()
        if prov.is_available():
            return prov
        logger.warning("Claude provider selected but ANTHROPIC_API_KEY is missing. Checking Gemini...")

    if provider_name == "gemini":
        prov = GeminiProvider()
        if prov.is_available():
            return prov
        logger.warning("Gemini provider selected but GEMINI_API_KEY is missing. Checking Ollama...")

    elif provider_name == "ollama":
        prov = OllamaProvider()
        if prov.is_available():
            return prov
        logger.warning("Ollama provider selected but endpoint unreachable. Falling back...")

    elif provider_name == "openai":
        prov = OpenAIProvider()
        if prov.is_available():
            return prov
        logger.warning("OpenAI provider selected but OPENAI_API_KEY is missing. Falling back...")

    # Secondary check: Ollama local running?
    ollama = OllamaProvider()
    if ollama.is_available():
        logger.info("Using local Ollama provider as fallback.")
        return ollama

    logger.warning("No live provider available. Using MockProvider.")
    return MockProvider()
