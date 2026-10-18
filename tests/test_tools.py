"""Unit tests for tool ecosystem."""
from app.security.policy import SecurityPolicy
from app.tools.registry import ToolRegistry
from app.tools.system_tool import SystemMonitorTool


def test_tool_registry_registration():
    registry = ToolRegistry()
    tools = registry.list_tools()
    assert len(tools) >= 5
    tool_names = [t["name"] for t in tools]
    assert "read_note" in tool_names
    assert "create_note" in tool_names
    assert "list_tasks" in tool_names
    assert "system_monitor" in tool_names


def test_system_monitor_tool():
    tool = SystemMonitorTool()
    res = tool.run()
    assert res.success is True
    assert "SO" in res.output
    assert res.metadata["cpu_cores"] > 0
