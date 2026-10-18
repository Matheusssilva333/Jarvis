"""Tool Registry and Execution Dispatcher."""
from __future__ import annotations

from typing import Any

from app.security.policy import SecurityPolicy
from app.tools.base import BaseTool, ToolResult
from app.tools.obsidian_tool import AppendDailyTool, CreateNoteTool, ReadNoteTool
from app.tools.system_tool import SystemMonitorTool
from app.tools.tasks_tool import AddTaskTool, CompleteTaskTool, ListTasksTool
from app.tools.terminal_tool import SafeTerminalTool


class ToolRegistry:
    """Central registry of all registered JARVIS tools."""

    def __init__(self, policy: SecurityPolicy | None = None):
        self.policy = policy or SecurityPolicy()
        self._tools: dict[str, BaseTool] = {}
        self._register_default_tools()

    def register(self, tool: BaseTool) -> None:
        tool.policy = self.policy
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "required_level": t.required_level.value,
                "level_name": t.required_level.name,
                "parameters": [
                    {
                        "name": p.name,
                        "type": p.param_type,
                        "description": p.description,
                        "required": p.required,
                        "default": p.default,
                    }
                    for p in t.parameters
                ],
            }
            for t in self._tools.values()
        ]

    def execute(self, tool_name: str, **kwargs) -> ToolResult:
        tool = self.get(tool_name)
        if not tool:
            return ToolResult(success=False, output=None, error=f"Ferramenta '{tool_name}' não encontrada.")
        return tool.run(**kwargs)

    def _register_default_tools(self) -> None:
        default_tools = [
            ReadNoteTool(self.policy),
            CreateNoteTool(self.policy),
            AppendDailyTool(self.policy),
            ListTasksTool(self.policy),
            AddTaskTool(self.policy),
            CompleteTaskTool(self.policy),
            SystemMonitorTool(self.policy),
            SafeTerminalTool(self.policy),
        ]
        for t in default_tools:
            self.register(t)
