"""Anthropic Claude API Provider."""
from __future__ import annotations

import time
import httpx

from app.core.config import logger, settings
from app.providers.base import BaseLLMProvider, ChatMessage, LLMResponse


class ClaudeProvider(BaseLLMProvider):
    """Integrates Anthropic Claude models (e.g. claude-3-5-sonnet-20241022, claude-3-haiku-20240307)."""

    def __init__(self, api_key: str | None = None, model: str = "claude-3-haiku-20240307"):
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model
        self.endpoint = "https://api.anthropic.com/v1/messages"

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def generate(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        if not self.is_available():
            raise RuntimeError("Anthropic API key is not configured.")

        start_time = time.time()
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        system_text = ""
        user_assistant_msgs = []

        for msg in messages:
            if msg.role == "system":
                system_text += msg.content + "\n\n"
            else:
                user_assistant_msgs.append({"role": msg.role, "content": msg.content})

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": user_assistant_msgs,
        }

        if system_text.strip():
            payload["system"] = system_text.strip()

        with httpx.Client(timeout=30.0) as client:
            res = client.post(self.endpoint, headers=headers, json=payload)
            res.raise_for_status()
            data = res.json()

        latency = time.time() - start_time
        content = data["content"][0]["text"]
        usage = data.get("usage", {})
        prompt_tokens = usage.get("input_tokens", 0)
        completion_tokens = usage.get("output_tokens", 0)

        return LLMResponse(
            content=content,
            model=self.model,
            provider="claude",
            tokens_prompt=prompt_tokens,
            tokens_completion=completion_tokens,
            latency_seconds=round(latency, 3),
        )
