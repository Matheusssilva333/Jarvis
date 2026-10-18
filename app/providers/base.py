"""Base LLM Provider abstraction and message structures."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generator, Literal

Role = Literal["system", "user", "assistant"]


@dataclass
class ChatMessage:
    role: Role
    content: str


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    tokens_prompt: int = 0
    tokens_completion: int = 0
    latency_seconds: float = 0.0


class BaseLLMProvider(ABC):
    """Abstract interface for all language model providers."""

    @abstractmethod
    def generate(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """Synchronously generate a completion for chat messages."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider credentials or endpoints are currently active."""
        pass
