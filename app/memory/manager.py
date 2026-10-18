"""Conversation and contextual memory management."""
from __future__ import annotations

from datetime import datetime
from app.providers.base import ChatMessage, Role


class ConversationMemory:
    """Manages short-term conversation context with sliding window pruning."""

    def __init__(self, max_history_turns: int = 8):
        self.max_history_turns = max_history_turns
        self.messages: list[ChatMessage] = []

    def add_user_message(self, content: str) -> None:
        self.messages.append(ChatMessage(role="user", content=content))
        self._prune()

    def add_assistant_message(self, content: str) -> None:
        self.messages.append(ChatMessage(role="assistant", content=content))
        self._prune()

    def get_messages(self, system_prompt: str | None = None) -> list[ChatMessage]:
        """Assemble full message list with optional system prompt."""
        result: list[ChatMessage] = []
        if system_prompt:
            result.append(ChatMessage(role="system", content=system_prompt))
        result.extend(self.messages)
        return result

    def clear(self) -> None:
        self.messages.clear()

    def _prune(self) -> None:
        """Keep only the latest N interaction turns."""
        max_messages = self.max_history_turns * 2
        if len(self.messages) > max_messages:
            self.messages = self.messages[-max_messages:]

    def export_as_markdown(self, title: str = "Conversa JARVIS") -> str:
        """Export session as Obsidian-compatible markdown note."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        lines = [
            "---",
            "type: chat-session",
            f"created: {now}",
            "tags:",
            "  - jarvis/chat",
            "---",
            f"# 💬 {title}",
            "",
        ]
        for msg in self.messages:
            sender = "🧑 Matheus" if msg.role == "user" else "🤖 JARVIS"
            lines.append(f"### {sender}")
            lines.append(msg.content)
            lines.append("")

        return "\n".join(lines)
