"""Obsidian Vault management tools for reading, writing, and appending."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.knowledge.parser import NoteParser
from app.knowledge.storage import KnowledgeStorage
from app.security.policy import SecurityLevel
from app.tools.base import BaseTool, ToolParameter, ToolResult


class ReadNoteTool(BaseTool):
    name = "read_note"
    description = "Lê o conteúdo integral de uma nota Markdown do cofre."
    required_level = SecurityLevel.READ_ONLY
    parameters = [
        ToolParameter(name="rel_path", param_type="string", description="Caminho relativo da nota no cofre"),
    ]

    def execute(self, rel_path: str, **kwargs) -> ToolResult:
        full_path = self.policy.validate_path_in_vault(settings.vault_path / rel_path)
        if not full_path.exists():
            return ToolResult(success=False, output=None, error=f"Nota não encontrada: '{rel_path}'")

        content = full_path.read_text(encoding="utf-8", errors="replace")
        return ToolResult(success=True, output=content, metadata={"path": rel_path})


class CreateNoteTool(BaseTool):
    name = "create_note"
    description = "Cria uma nova nota no cofre com validação de caminho e snapshot preventivo."
    required_level = SecurityLevel.CONTROLLED_WRITE
    parameters = [
        ToolParameter(name="rel_path", param_type="string", description="Caminho relativo de destino (ex: '01 Diário/Nota.md')"),
        ToolParameter(name="content", param_type="string", description="Conteúdo Markdown da nota"),
        ToolParameter(name="overwrite", param_type="boolean", description="Se permite sobrescrever caso exista", default=False),
    ]

    def execute(self, rel_path: str, content: str, overwrite: bool = False, **kwargs) -> ToolResult:
        full_path = self.policy.validate_path_in_vault(settings.vault_path / rel_path)

        if full_path.exists():
            if not overwrite:
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"A nota '{rel_path}' já existe. Defina overwrite=True para atualizar.",
                )
            # Create snapshot backup
            self.policy.create_snapshot(full_path)

        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")

        # Update index immediately
        parser = NoteParser()
        parsed = parser.parse_content(content, rel_path, full_path.stat().st_mtime)
        storage = KnowledgeStorage()
        storage.save_note(parsed)

        return ToolResult(
            success=True,
            output=f"Nota criada com sucesso em: '{rel_path}'",
            metadata={"rel_path": rel_path, "bytes": len(content.encode('utf-8'))},
        )


class AppendDailyTool(BaseTool):
    name = "append_daily"
    description = "Anexa uma ideia, reflexão ou vitória na seção apropriada da nota diária de hoje."
    required_level = SecurityLevel.CONTROLLED_WRITE
    parameters = [
        ToolParameter(name="section", param_type="string", description="Nome da seção (ex: 'Ideias', 'Vitórias', 'Log')"),
        ToolParameter(name="entry", param_type="string", description="Texto a ser adicionado"),
    ]

    def execute(self, section: str, entry: str, **kwargs) -> ToolResult:
        today_str = datetime.now().strftime("%d/%m/%Y")
        today_file_name = f"Diário {datetime.now().strftime('%Y-%m-%d')}.md"
        daily_path = settings.vault_path / "01 Diário" / today_file_name

        # Validate path
        self.policy.validate_path_in_vault(daily_path)

        if not daily_path.exists():
            # Create base daily note if not existing
            initial_content = (
                f"---\ntype: daily\ncreated: {datetime.now().strftime('%Y-%m-%d')}\ntags:\n  - daily/📅\n---\n\n"
                f"# 📅 Diário: {today_str}\n\n"
                f"## 🎯 Prioridades de Hoje\n\n"
                f"## 💡 Ideias e Insights (Captura Rápida)\n\n"
                f"## 📝 Log de Pensamentos\n\n"
                f"## ✅ Vitórias do Dia\n\n"
            )
            daily_path.parent.mkdir(parents=True, exist_ok=True)
            daily_path.write_text(initial_content, encoding="utf-8")

        # Backup snapshot before append
        self.policy.create_snapshot(daily_path)
        content = daily_path.read_text(encoding="utf-8")

        # Target section append
        bullet = f"- {entry.strip()}\n"
        matched = False
        new_lines = []
        target_header_lower = section.lower()

        for line in content.splitlines(keepends=True):
            new_lines.append(line)
            if line.startswith("#") and target_header_lower in line.lower():
                new_lines.append(bullet)
                matched = True

        if not matched:
            new_lines.append(f"\n## {section}\n{bullet}")

        updated_content = "".join(new_lines)
        daily_path.write_text(updated_content, encoding="utf-8")

        # Update index
        rel_path = f"01 Diário/{today_file_name}"
        parser = NoteParser()
        parsed = parser.parse_content(updated_content, rel_path, daily_path.stat().st_mtime)
        storage = KnowledgeStorage()
        storage.save_note(parsed)

        return ToolResult(
            success=True,
            output=f"Entrada anexada com sucesso ao diário de hoje sob a seção '{section}'.",
            metadata={"daily_file": str(daily_path.name)},
        )
