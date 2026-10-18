"""SAO System v2.0 - Realistic Gamification Engine for Matheus Silva."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.config import logger, settings
from app.knowledge.storage import KnowledgeStorage


@dataclass
class PlayerStats:
    name: str = "Matheus Silva"
    title: str = "Sentinela Atalaia / Engenheiro"
    rank: str = "Rank A"
    level: int = 1
    xp: int = 0
    next_level_xp: int = 100
    tasks_completed_lifetime: int = 0
    tasks_completed_today: int = 0
    last_audit_date: str = ""

    def calculate_rank(self) -> str:
        """Determines player Rank based on Level progression."""
        if self.level >= 50:
            return "Rank S (Soberano)"
        if self.level >= 30:
            return "Rank A (Elite Industrial)"
        if self.level >= 20:
            return "Rank B (Veterano)"
        if self.level >= 10:
            return "Rank C (Praticante Avançado)"
        if self.level >= 5:
            return "Rank D (Iniciado)"
        return "Rank E (Recruta)"


class SAOSystemManager:
    """Processes daily XP from verified tasks, enforces audit logs, and updates player stats."""

    def __init__(self, storage: KnowledgeStorage | None = None):
        self.storage = storage or KnowledgeStorage()
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Create player_stats table in SQLite if not present."""
        with self.storage.get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS player_stats (
                    id INTEGER PRIMARY KEY,
                    data_json TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def get_stats(self) -> PlayerStats:
        """Load player stats from SQLite or calculate from all-time completed tasks."""
        with self.storage.get_connection() as conn:
            row = conn.execute("SELECT data_json FROM player_stats WHERE id = 1;").fetchone()
            if row:
                d = json.loads(row["data_json"])
                return PlayerStats(**d)

        # First-time calculation from indexed tasks in vault
        all_completed = self.storage.get_tasks(completed=True, limit=1000)
        total_tasks = len(all_completed)
        total_xp = total_tasks * settings.xp_per_task
        level = max(1, (total_xp // 100) + 1)
        next_xp = level * 100

        stats = PlayerStats(
            level=level,
            xp=total_xp,
            next_level_xp=next_xp,
            tasks_completed_lifetime=total_tasks,
            last_audit_date=datetime.now().strftime("%Y-%m-%d"),
        )
        stats.rank = stats.calculate_rank()
        self.save_stats(stats)
        return stats

    def save_stats(self, stats: PlayerStats) -> None:
        """Persist stats to SQLite and write to 05 System/Player Stats.md."""
        data_str = json.dumps(asdict(stats), ensure_ascii=False)
        with self.storage.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO player_stats (id, data_json, updated_at)
                VALUES (1, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(id) DO UPDATE SET
                    data_json=excluded.data_json,
                    updated_at=CURRENT_TIMESTAMP;
                """,
                (data_str,),
            )
        self.sync_to_obsidian_file(stats)

    def process_daily(self, date_str: str | None = None) -> dict[str, Any]:
        """Audit completed tasks for the given date, compute XP, and check level up."""
        today = date_str or datetime.now().strftime("%Y-%m-%d")

        with self.storage.get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, description, note_path FROM tasks WHERE completed = 1 AND completed_date = ?;",
                (today,),
            )
            tasks_today = [dict(r) for r in cursor]

            # In case completed_date is not explicitly set with checkmark, check daily note of today
            if not tasks_today:
                cursor = conn.execute(
                    "SELECT id, description, note_path FROM tasks WHERE completed = 1 AND note_path LIKE ?;",
                    (f"%{today}%",),
                )
                tasks_today = [dict(r) for r in cursor]

        stats = self.get_stats()
        count = len(tasks_today)
        xp_earned = count * settings.xp_per_task

        stats.xp += xp_earned
        stats.tasks_completed_today = count
        stats.tasks_completed_lifetime += count
        stats.last_audit_date = today

        # Level calculation (múltiplos de 100 XP)
        old_level = stats.level
        new_level = max(1, (stats.xp // 100) + 1)
        stats.level = new_level
        stats.next_level_xp = new_level * 100
        stats.rank = stats.calculate_rank()

        leveled_up = new_level > old_level
        self.save_stats(stats)

        return {
            "date": today,
            "tasks_count": count,
            "xp_earned": xp_earned,
            "total_xp": stats.xp,
            "level": stats.level,
            "leveled_up": leveled_up,
            "rank": stats.rank,
            "tasks": tasks_today,
        }

    def sync_to_obsidian_file(self, stats: PlayerStats) -> None:
        """Write stats to ⚔️ Centro de Comando/Status do Jogador.md in Obsidian."""
        hud_dir = settings.vault_path / "⚔️ Centro de Comando"
        hud_dir.mkdir(parents=True, exist_ok=True)
        stats_file = hud_dir / "Status do Jogador.md"

        content = (
            f"---\n"
            f"tipo: perfil-jogador\n"
            f"jogador: {stats.name}\n"
            f"titulo: {stats.title}\n"
            f"rank: {stats.rank}\n"
            f"nivel: {stats.level}\n"
            f"xp: {stats.xp}\n"
            f"xp_proximo_nivel: {stats.next_level_xp}\n"
            f"tarefas_lifetime: {stats.tasks_completed_lifetime}\n"
            f"tarefas_hoje: {stats.tasks_completed_today}\n"
            f"ultima_auditoria: \"{stats.last_audit_date}\"\n"
            f"fonte: Supabase rpg_player_state\n"
            f"cssclasses:\n"
            f"  - rpg-dashboard\n"
            f"---\n\n"
            f"# 🛡️ STATUS DO JOGADOR — SAO SYSTEM v2.0\n\n"
            f"> [!quote] *\"A vida é um log de auditoria. Ou há Evidência (XP) ou há Ruído (Falha).\"*\n\n"
            f"---\n\n"
            f"## 👤 Identidade do Sentinela\n\n"
            f"- **Jogador:** `{stats.name}`\n"
            f"- **Título:** `{stats.title}`\n"
            f"- **Rank Atual:** `{stats.rank}`\n"
            f"- **Nível Atual:** **Level {stats.level}**\n\n"
            f"### ⚡ Barra de Experiência (XP)\n\n"
            f"```\n"
            f"Progresso: [{stats.xp} / {stats.next_level_xp} XP]\n"
            f"```\n\n"
            f"## 📊 Estatísticas Vitais\n\n"
            f"| Atributo | Valor | Fonte |\n"
            f"|---|---|---|\n"
            f"| ⚔️ Nível | Level {stats.level} | Sistema SAO |\n"
            f"| ✨ XP Total | {stats.xp} XP | Auditoria Diária |\n"
            f"| 🏆 Próximo Nível | {stats.next_level_xp} XP | Meta de Nível |\n"
            f"| 📜 Tarefas Históricas | {stats.tasks_completed_lifetime} concluídas | SQLite + Supabase |\n"
            f"| 📅 Última Auditoria | {stats.last_audit_date} | Sentinela Core |\n\n"
            f"---\n\n"
            f"> [!NOTE] *O Binário do Caráter:* Sem evidência, o XP é negado. Sem revisão, não há Rank.\n"
        )

        try:
            stats_file.write_text(content, encoding="utf-8")
            logger.info("Status do Jogador.md sincronizado no cofre com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao salvar Status do Jogador.md: {e}")
