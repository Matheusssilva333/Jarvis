"""Knowledge retrieval interface providing lexical, graph, and contextual search."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.config import logger, settings
from app.knowledge.storage import KnowledgeStorage


@dataclass
class SearchResult:
    note_path: str
    title: str
    heading: str
    content: str
    snippet: str
    score: float
    tags: str = ""


class KnowledgeRetriever:
    """Retrieves relevant knowledge chunks, task metrics, and link networks."""

    def __init__(self, storage: KnowledgeStorage | None = None):
        self.storage = storage or KnowledgeStorage()

    def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        """Perform search over notes and sections using BM25 ranking."""
        raw_results = self.storage.search_fts(query=query, limit=limit)
        results: list[SearchResult] = []

        for row in raw_results:
            results.append(
                SearchResult(
                    note_path=row["note_path"],
                    title=row["title"],
                    heading=row["heading"],
                    content=row["content"],
                    snippet=row.get("snippet", ""),
                    score=float(row["rank"]),
                    tags=row.get("tags", ""),
                )
            )
        return results

    def get_tasks(
        self,
        completed: bool | None = None,
        search: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Retrieve tasks with optional completion and description filtering."""
        return self.storage.get_tasks(completed=completed, search=search, limit=limit)

    def get_links_and_backlinks(self, note_title: str, note_path: str | None = None) -> dict[str, Any]:
        """Retrieve both outgoing connections and incoming backlinks for a given note."""
        outgoing: list[str] = []
        if note_path:
            outgoing = self.storage.get_links_from(note_path)

        backlinks = self.storage.get_backlinks_to(note_title)

        return {
            "title": note_title,
            "outgoing_links": outgoing,
            "incoming_backlinks": backlinks,
        }

    def get_summary_context(self) -> dict[str, Any]:
        """Return system-wide statistics for system prompt injection."""
        return self.storage.get_stats()
