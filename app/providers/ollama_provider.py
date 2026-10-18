"""Ollama Local LLM Provider."""
from __future__ import annotations

import time
import httpx

from app.core.config import logger, settings
from app.providers.base import BaseLLMProvider, ChatMessage, LLMResponse


class OllamaProvider(BaseLLMProvider):
    """Integrates local Ollama models (e.g. qwen2.5:1.5b-instruct, phi3:mini)."""

    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model

    def is_available(self) -> bool:
        try:
            with httpx.Client(timeout=1.5) as client:
                res = client.get(f"{self.base_url}/api/tags")
                if res.status_code != 200:
                    return False
                models = [m.get("name", "") for m in res.json().get("models", [])]
                # Check if configured model or model prefix is downloaded
                return any(self.model in m or m.startswith(self.model) for m in models)
        except Exception:
            return False

    def generate(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        start_time = time.time()
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                res = client.post(url, json=payload)
                res.raise_for_status()
                data = res.json()
        except Exception as e:
            logger.error(f"Ollama execution error: {e}")
            raise RuntimeError(f"Ollama model '{self.model}' failed: {e}") from e

        latency = time.time() - start_time
        content = data.get("message", {}).get("content", "")
        prompt_eval = data.get("prompt_eval_count", 0)
        eval_count = data.get("eval_count", 0)

        return LLMResponse(
            content=content,
            model=self.model,
            provider="ollama",
            tokens_prompt=prompt_eval,
            tokens_completion=eval_count,
            latency_seconds=round(latency, 3),
        )
