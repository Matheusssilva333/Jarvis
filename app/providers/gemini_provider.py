"""Google Gemini API Provider implementation via REST endpoint."""
from __future__ import annotations

import time
import httpx

from app.core.config import logger, settings
from app.providers.base import BaseLLMProvider, ChatMessage, LLMResponse


class GeminiProvider(BaseLLMProvider):
    """Integrates Google Gemini models (e.g. gemini-2.5-flash, gemini-1.5-flash)."""

    def __init__(self, api_key: str | None = None, model: str = "gemini-2.5-flash"):
        self.api_key = api_key or settings.gemini_api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def generate(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        if not self.is_available():
            raise RuntimeError(
                "Gemini API key is not configured. Set GEMINI_API_KEY in jarvis/.env"
            )

        start_time = time.time()
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

        # Convert chat messages to Gemini content format
        contents = []
        system_instruction = None

        for msg in messages:
            if msg.role == "system":
                system_instruction = {"parts": [{"text": msg.content}]}
            else:
                role = "user" if msg.role == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg.content}]})

        payload: dict = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        if system_instruction:
            payload["systemInstruction"] = system_instruction

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code != 200:
                logger.error(f"Gemini API error {resp.status_code}: {resp.text}")
                resp.raise_for_status()

            data = resp.json()

        latency = time.time() - start_time

        try:
            candidate = data["candidates"][0]
            text = candidate["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as err:
            logger.error(f"Failed to parse Gemini response: {data}")
            raise RuntimeError("Malformed response from Gemini API") from err

        usage = data.get("usageMetadata", {})
        prompt_tokens = usage.get("promptTokenCount", 0)
        completion_tokens = usage.get("candidatesTokenCount", 0)

        return LLMResponse(
            content=text,
            model=self.model,
            provider="gemini",
            tokens_prompt=prompt_tokens,
            tokens_completion=completion_tokens,
            latency_seconds=round(latency, 3),
        )
