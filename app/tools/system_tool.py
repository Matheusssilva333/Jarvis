"""System diagnostics and hardware telemetry tool."""
from __future__ import annotations

import os
import platform
import shutil
from typing import Any

from app.security.policy import SecurityLevel
from app.tools.base import BaseTool, ToolResult


class SystemMonitorTool(BaseTool):
    name = "system_monitor"
    description = "Obtém métricas em tempo real sobre o hardware do computador (CPU, RAM, Disco)."
    required_level = SecurityLevel.READ_ONLY

    def execute(self, **kwargs) -> ToolResult:
        disk_usage = shutil.disk_usage(os.getcwd())
        free_gb = round(disk_usage.free / (1024**3), 2)
        total_gb = round(disk_usage.total / (1024**3), 2)
        used_gb = round(disk_usage.used / (1024**3), 2)

        data = {
            "os": f"{platform.system()} {platform.release()} ({platform.architecture()[0]})",
            "cpu": platform.processor(),
            "cpu_cores": os.cpu_count(),
            "disk": {
                "total_gb": total_gb,
                "used_gb": used_gb,
                "free_gb": free_gb,
                "percent_free": round((disk_usage.free / disk_usage.total) * 100, 1),
            },
            "python": platform.python_version(),
        }

        output = (
            f"**Diagnóstico de Sistema & Hardware:**\n"
            f"- **SO:** {data['os']}\n"
            f"- **Processador:** {data['cpu']} ({data['cpu_cores']} núcleos)\n"
            f"- **Disco Local:** {used_gb} GB usados / {free_gb} GB livres ({total_gb} GB total)\n"
            f"- **Python:** v{data['python']}"
        )

        return ToolResult(success=True, output=output, metadata=data)
