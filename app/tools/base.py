"""Base classes and types for JARVIS tool ecosystem."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.security.policy import SecurityLevel, SecurityPolicy


@dataclass
class ToolParameter:
    name: str
    param_type: str
    description: str
    required: bool = True
    default: Any = None


@dataclass
class ToolResult:
    success: bool
    output: Any
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseTool(ABC):
    """Abstract base class for all operational tools."""

    name: str
    description: str
    required_level: SecurityLevel = SecurityLevel.READ_ONLY
    parameters: list[ToolParameter] = []

    def __init__(self, policy: SecurityPolicy | None = None):
        self.policy = policy or SecurityPolicy()

    def run(self, **kwargs) -> ToolResult:
        """Enforces security policy before execution."""
        try:
            self.policy.check_permission(self.required_level, f"Execução da ferramenta '{self.name}'")
            return self.execute(**kwargs)
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Core tool logic implemented by subclasses."""
        pass
