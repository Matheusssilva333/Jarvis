"""Security policies, authorization tiers (L1 to L4), and guardrails."""
from __future__ import annotations

import re
import shutil
from datetime import datetime
from enum import IntEnum
from pathlib import Path
from typing import Any

from app.core.config import logger, settings


class SecurityLevel(IntEnum):
    READ_ONLY = 1
    CONTROLLED_WRITE = 2
    EXECUTION = 3
    CRITICAL_ADMIN = 4


class SecurityViolationError(PermissionError):
    """Raised when an operation exceeds current security authorization."""
    pass


class DangerousCommandError(ValueError):
    """Raised when a command matches dangerous or destructive system patterns."""
    pass


class SecurityPolicy:
    """Enforces authorization levels, directory boundaries, and execution guardrails."""

    DANGEROUS_PATTERNS = [
        re.compile(r"\brmdir\s+/s\b", re.I),
        re.compile(r"\bdel\s+/[fsq]\b", re.I),
        re.compile(r"\bformat\s+[a-z]:\b", re.I),
        re.compile(r"\brm\s+-(?:r|rf|fr)\b", re.I),
        re.compile(r"\bdrop\s+(?:database|table)\b", re.I),
        re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", re.I),
        re.compile(r"\bdiskpart\b", re.I),
        re.compile(r"\bshutdown\s+/[rs]\b", re.I),
    ]

    def __init__(self, current_level: int | None = None):
        self.current_level = SecurityLevel(current_level or settings.security_level)

    def check_permission(self, required_level: SecurityLevel, action_desc: str) -> None:
        """Verify that current system level satisfies the required operation level."""
        if self.current_level < required_level:
            raise SecurityViolationError(
                f"Ação negada: '{action_desc}' requer Nível {required_level.name} ({required_level.value}), "
                f"mas o sistema está operando no Nível {self.current_level.name} ({self.current_level.value})."
            )

    def validate_path_in_vault(self, target_path: Path | str) -> Path:
        """Ensure the target path is strictly inside the Obsidian Vault directory."""
        resolved = Path(target_path).resolve()
        vault_root = settings.vault_path.resolve()

        if not str(resolved).startswith(str(vault_root)):
            raise SecurityViolationError(
                f"Acesso negado: Caminho '{resolved}' fora dos limites do cofre '{vault_root}'."
            )
        return resolved

    def validate_command(self, command: str) -> None:
        """Check for destructive command signatures."""
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.search(command):
                raise DangerousCommandError(
                    f"Comando bloqueado pelo Sentinela: Assinatura de alto risco detectada em '{command}'."
                )

    def create_snapshot(self, target_file: Path) -> Path | None:
        """Create a versioned backup before modifying any note in the vault."""
        if not target_file.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{target_file.stem}_{timestamp}{target_file.suffix}"
        backup_path = settings.backups_dir / backup_name

        shutil.copy2(target_file, backup_path)
        logger.info(f"Snapshot seguro gerado em: {backup_path}")
        return backup_path
