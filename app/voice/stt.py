"""Speech-To-Text (STT) interface and pipeline."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class BaseSTT(ABC):
    """Abstract interface for Speech-to-Text transcription."""

    @abstractmethod
    def transcribe(self, audio_path: Path | str) -> str:
        pass


class MockSTT(BaseSTT):
    """Fallback audio transcriber for test environments."""

    def transcribe(self, audio_path: Path | str) -> str:
        return "Jarvis, quais são minhas prioridades de hoje?"
