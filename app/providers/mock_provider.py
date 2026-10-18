"""Mock LLM Provider for offline execution, unit tests, and validation."""
from __future__ import annotations

import time

from app.providers.base import BaseLLMProvider, ChatMessage, LLMResponse


class MockProvider(BaseLLMProvider):
    """Deterministic provider that echoes context or returns simulated synthesis."""

    def __init__(self, response_text: str | None = None):
        self.response_text = response_text

    def is_available(self) -> bool:
        return True

    def generate(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        start_time = time.time()
        last_msg = messages[-1].content if messages else "Nenhuma mensagem."

        if self.response_text:
            text = self.response_text
        else:
            text = (
                f"[MODO OFFLINE/DEMO]\n"
                f"Entendido. Processei sua solicitação com base nos dados do cofre.\n"
                f"Mensagem recebida: {last_msg[:120]}..."
            )

        return LLMResponse(
            content=text,
            model="mock-sentinela-v1",
            provider="mock",
            tokens_prompt=len(last_msg) // 4,
            tokens_completion=len(text) // 4,
            latency_seconds=round(time.time() - start_time, 4),
        )
