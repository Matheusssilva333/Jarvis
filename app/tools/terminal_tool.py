"""Controlled terminal execution tool with Level 3 authorization."""
from __future__ import annotations

import subprocess
from app.security.policy import SecurityLevel
from app.tools.base import BaseTool, ToolParameter, ToolResult


class SafeTerminalTool(BaseTool):
    name = "terminal_run"
    description = "Executa um comando no terminal do sistema (Requer Nível 3 - Execução)."
    required_level = SecurityLevel.EXECUTION
    parameters = [
        ToolParameter(name="command", param_type="string", description="Comando shell a ser executado"),
        ToolParameter(name="timeout", param_type="integer", description="Tempo limite em segundos", required=False, default=15),
    ]

    def execute(self, command: str, timeout: int = 15, **kwargs) -> ToolResult:
        # Validate against destructive signatures
        self.policy.validate_command(command)

        try:
            res = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace",
            )
            stdout = res.stdout.strip()
            stderr = res.stderr.strip()

            output = stdout if stdout else (stderr if stderr else "Comando executado sem retorno.")
            success = res.returncode == 0

            return ToolResult(
                success=success,
                output=output,
                error=stderr if not success else None,
                metadata={"returncode": res.returncode, "command": command},
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output=None,
                error=f"Tempo limite excedido ({timeout}s) ao executar: '{command}'",
            )
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))
