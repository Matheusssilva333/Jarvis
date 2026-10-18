"""Task management tools for Obsidian Tasks."""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.knowledge.parser import NoteParser
from app.knowledge.storage import KnowledgeStorage
from app.security.policy import SecurityLevel
from app.tools.base import BaseTool, ToolParameter, ToolResult


class ListTasksTool(BaseTool):
    name = "list_tasks"
    description = "Lista tarefas pendentes ou concluídas do cofre com filtros."
    required_level = SecurityLevel.READ_ONLY
    parameters = [
        ToolParameter(name="completed", param_type="boolean", description="Filtrar por status concluído (True/False ou None para todos)", required=False, default=None),
        ToolParameter(name="search", param_type="string", description="Termo de busca na descrição", required=False, default=None),
        ToolParameter(name="limit", param_type="integer", description="Número máximo de tarefas", required=False, default=30),
    ]

    def execute(self, completed: bool | None = None, search: str | None = None, limit: int = 30, **kwargs) -> ToolResult:
        storage = KnowledgeStorage()
        tasks = storage.get_tasks(completed=completed, search=search, limit=limit)
        return ToolResult(success=True, output=tasks, metadata={"count": len(tasks)})


class AddTaskTool(BaseTool):
    name = "add_task"
    description = "Insere uma nova tarefa no padrão Obsidian Tasks em uma nota."
    required_level = SecurityLevel.CONTROLLED_WRITE
    parameters = [
        ToolParameter(name="rel_path", param_type="string", description="Caminho relativo da nota (ex: '01 Diário/Nota.md')"),
        ToolParameter(name="description", param_type="string", description="Descrição da tarefa"),
        ToolParameter(name="due_date", param_type="string", description="Data limite no formato AAAA-MM-DD", required=False, default=None),
        ToolParameter(name="priority", param_type="string", description="Prioridade: 'high' ou 'low'", required=False, default=None),
    ]

    def execute(self, rel_path: str, description: str, due_date: str | None = None, priority: str | None = None, **kwargs) -> ToolResult:
        full_path = self.policy.validate_path_in_vault(settings.vault_path / rel_path)
        if not full_path.exists():
            return ToolResult(success=False, output=None, error=f"Nota não encontrada: '{rel_path}'")

        self.policy.create_snapshot(full_path)
        content = full_path.read_text(encoding="utf-8")

        # Format task line
        task_line = f"- [ ] {description}"
        if due_date:
            task_line += f" 📅 {due_date}"
        if priority == "high":
            task_line += " ⏫"
        elif priority == "low":
            task_line += " 🔽"

        # Append to Prioridades / Tarefas heading if exists, else append to bottom
        lines = content.splitlines(keepends=True)
        inserted = False
        new_lines = []

        for line in lines:
            new_lines.append(line)
            if not inserted and any(h in line.lower() for h in ["## 🎯 prioridades", "## tarefas", "## todo"]):
                new_lines.append(task_line + "\n")
                inserted = True

        if not inserted:
            new_lines.append("\n" + task_line + "\n")

        updated_content = "".join(new_lines)
        full_path.write_text(updated_content, encoding="utf-8")

        # Update index
        parser = NoteParser()
        parsed = parser.parse_content(updated_content, rel_path, full_path.stat().st_mtime)
        storage = KnowledgeStorage()
        storage.save_note(parsed)

        return ToolResult(
            success=True,
            output=f"Tarefa adicionada: '{task_line}' em [[{rel_path}]]",
            metadata={"task": task_line, "file": rel_path},
        )


class CompleteTaskTool(BaseTool):
    name = "complete_task"
    description = "Marca uma tarefa como concluída (- [x]) com data de finalização."
    required_level = SecurityLevel.CONTROLLED_WRITE
    parameters = [
        ToolParameter(name="rel_path", param_type="string", description="Caminho relativo da nota que contém a tarefa"),
        ToolParameter(name="task_pattern", param_type="string", description="Trecho de texto que identifica a tarefa"),
    ]

    def execute(self, rel_path: str, task_pattern: str, **kwargs) -> ToolResult:
        full_path = self.policy.validate_path_in_vault(settings.vault_path / rel_path)
        if not full_path.exists():
            return ToolResult(success=False, output=None, error=f"Nota não encontrada: '{rel_path}'")

        self.policy.create_snapshot(full_path)
        content = full_path.read_text(encoding="utf-8")
        today = datetime.now().strftime("%Y-%m-%d")

        lines = content.splitlines(keepends=True)
        found = False
        new_lines = []

        for line in lines:
            if not found and re.match(r"^\s*-\s*\[\s*\]", line) and task_pattern.lower() in line.lower():
                # Replace - [ ] with - [x] and append completion date if not present
                replaced = re.sub(r"^(\s*-\s*\[)\s*(\])", r"\g<1>x\2", line)
                if "✅" not in replaced:
                    replaced = replaced.rstrip("\r\n") + f" ✅ {today}\n"
                new_lines.append(replaced)
                found = True
            else:
                new_lines.append(line)

        if not found:
            return ToolResult(
                success=False,
                output=None,
                error=f"Nenhuma tarefa pendente correspondente a '{task_pattern}' foi encontrada em '{rel_path}'.",
            )

        updated_content = "".join(new_lines)
        full_path.write_text(updated_content, encoding="utf-8")

        # Update index
        parser = NoteParser()
        parsed = parser.parse_content(updated_content, rel_path, full_path.stat().st_mtime)
        storage = KnowledgeStorage()
        storage.save_note(parsed)

        return ToolResult(
            success=True,
            output=f"Tarefa concluída com sucesso: '{task_pattern}' em [[{rel_path}]]",
            metadata={"file": rel_path, "completed_date": today},
        )
