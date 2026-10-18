"""OpenAI & OpenAI-compatible LLM Provider."""
from __future__ import annotations

import time
import httpx

from app.core.config import logger, settings
from app.providers.base import BaseLLMProvider, ChatMessage, LLMResponse


class OpenAIProvider(BaseLLMProvider):
    """Integrates OpenAI and compatible APIs (e.g. gpt-4o-mini, Groq, OpenRouter)."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
    ):
        self.api_key = api_key or settings.openai_api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def generate(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        if not self.is_available():
            raise RuntimeError("OpenAI API key is not configured.")

        start_time = time.time()
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        with httpx.Client(timeout=30.0) as client:
            res = client.post(url, headers=headers, json=payload)
            res.raise_for_status()
            data = res.json()

        latency = time.time() - start_time
        choice = data["choices"][0]
        content = choice["message"]["content"]
        usage = data.get("usage", {})

        return LLMResponse(
            content=content,
            model=self.model,
            provider="openai",
            tokens_prompt=usage.get("prompt_tokens", 0),
            tokens_completion=usage.get("completion_tokens", 0),
            latency_seconds=round(latency, 3),
        )
