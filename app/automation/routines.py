"""Advanced personal automations and audit routines."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from app.core.config import settings
from app.knowledge.storage import KnowledgeStorage
from app.sao.manager import SAOSystemManager


class AutomationRoutines:
    """Executes high-level audit workflows over the Obsidian Vault."""

    def __init__(self, storage: KnowledgeStorage | None = None):
        self.storage = storage or KnowledgeStorage()
        self.sao = SAOSystemManager(storage=self.storage)

    def run_daily_review(self) -> dict[str, Any]:
        """Audit today's activities, complete tasks check, and XP synchronization."""
        today = datetime.now().strftime("%Y-%m-%d")
        sao_res = self.sao.process_daily(today)
        pending = self.storage.get_tasks(completed=False, limit=10)

        report = {
            "date": today,
            "tasks_completed_today": sao_res["tasks_count"],
            "xp_earned": sao_res["xp_earned"],
            "level": sao_res["level"],
            "rank": sao_res["rank"],
            "top_pending_priorities": [t["description"] for t in pending[:5]],
        }
        return report

    def find_knowledge_gaps(self) -> list[dict[str, Any]]:
        """Identify referenced notes (wikilinks) that do not yet exist in the vault."""
        with self.storage.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT 
                    nl.target_title,
                    COUNT(nl.source_path) as reference_count,
                    GROUP_CONCAT(nl.source_path, ', ') as referenced_in
                FROM note_links nl
                LEFT JOIN notes n ON n.title = nl.target_title OR n.path LIKE '%' || nl.target_title || '.md'
                WHERE n.path IS NULL 
                  AND nl.target_title NOT LIKE '%.png' 
                  AND nl.target_title NOT LIKE '%.jpg'
                  AND nl.target_title NOT LIKE '%.pdf'
                GROUP BY nl.target_title
                ORDER BY reference_count DESC
                LIMIT 15;
                """
            )
            return [dict(r) for r in cursor]

    def generate_weekly_digest(self) -> dict[str, Any]:
        """Synthesize vault activity from the last 7 days."""
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        with self.storage.get_connection() as conn:
            notes_recent = conn.execute(
                "SELECT path, title, word_count FROM notes WHERE last_indexed >= ?;", (week_ago,)
            ).fetchall()
            completed_recent = conn.execute(
                "SELECT COUNT(*) FROM tasks WHERE completed = 1 AND (completed_date >= ? OR completed_date IS NULL);",
                (week_ago,),
            ).fetchone()[0]

        return {
            "since": week_ago,
            "notes_modified_count": len(notes_recent),
            "tasks_completed_count": completed_recent,
            "recent_notes": [r["title"] for r in notes_recent[:10]],
        }
