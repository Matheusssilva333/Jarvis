"""SQLite storage engine with FTS5 and relational graphs."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

from app.core.config import logger, settings
from app.knowledge.parser import ParsedNote, ParsedTask


class KnowledgeStorage:
    """Manages SQLite storage, FTS5 full-text indexing, and note graphs."""

    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or settings.db_path
        self._init_db()

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Create database schema if not present."""
        with self.get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS notes (
                    path TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    mtime REAL NOT NULL,
                    sha256 TEXT NOT NULL,
                    note_type TEXT DEFAULT 'general',
                    tags TEXT,
                    wikilinks TEXT,
                    word_count INTEGER DEFAULT 0,
                    last_indexed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS note_sections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    note_path TEXT NOT NULL REFERENCES notes(path) ON DELETE CASCADE,
                    heading TEXT NOT NULL,
                    level INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    token_estimate INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS note_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_path TEXT NOT NULL REFERENCES notes(path) ON DELETE CASCADE,
                    target_title TEXT NOT NULL,
                    link_type TEXT DEFAULT 'wikilink'
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    note_path TEXT NOT NULL REFERENCES notes(path) ON DELETE CASCADE,
                    line_num INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    completed INTEGER NOT NULL,
                    due_date TEXT,
                    completed_date TEXT,
                    priority TEXT,
                    raw_text TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(completed);
                CREATE INDEX IF NOT EXISTS idx_note_links_target ON note_links(target_title);
                CREATE INDEX IF NOT EXISTS idx_note_sections_path ON note_sections(note_path);

                -- Virtual FTS5 table for full-text search
                CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
                    note_path UNINDEXED,
                    title,
                    heading,
                    content,
                    tags,
                    tokenize='unicode61 remove_diacritics 2'
                );
                """
            )
        logger.debug(f"Knowledge database initialized at {self.db_path}")

    def get_indexed_notes_map(self) -> dict[str, tuple[float, str]]:
        """Return a mapping of path -> (mtime, sha256) for quick incremental comparison."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT path, mtime, sha256 FROM notes;")
            return {row["path"]: (row["mtime"], row["sha256"]) for row in cursor}

    def save_note(self, note: ParsedNote) -> None:
        """Atomically persist or replace a note and its child entities in the database."""
        with self.get_connection() as conn:
            # 1. Delete old sub-entities and FTS records
            conn.execute("DELETE FROM notes_fts WHERE note_path = ?;", (note.rel_path,))
            conn.execute("DELETE FROM note_sections WHERE note_path = ?;", (note.rel_path,))
            conn.execute("DELETE FROM note_links WHERE source_path = ?;", (note.rel_path,))
            conn.execute("DELETE FROM tasks WHERE note_path = ?;", (note.rel_path,))

            # 2. Upsert main note record
            tags_json = json.dumps(note.tags, ensure_ascii=False)
            wikilinks_json = json.dumps(note.wikilinks, ensure_ascii=False)

            conn.execute(
                """
                INSERT INTO notes (path, title, mtime, sha256, note_type, tags, wikilinks, word_count, last_indexed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(path) DO UPDATE SET
                    title=excluded.title,
                    mtime=excluded.mtime,
                    sha256=excluded.sha256,
                    note_type=excluded.note_type,
                    tags=excluded.tags,
                    wikilinks=excluded.wikilinks,
                    word_count=excluded.word_count,
                    last_indexed=CURRENT_TIMESTAMP;
                """,
                (
                    note.rel_path,
                    note.title,
                    note.mtime,
                    note.sha256,
                    note.note_type,
                    tags_json,
                    wikilinks_json,
                    note.word_count,
                ),
            )

            # 3. Insert Sections
            for sec in note.sections:
                conn.execute(
                    """
                    INSERT INTO note_sections (note_path, heading, level, content, token_estimate)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (note.rel_path, sec.heading, sec.level, sec.content, sec.token_estimate),
                )
                # Insert into FTS5 for each section
                conn.execute(
                    """
                    INSERT INTO notes_fts (note_path, title, heading, content, tags)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (note.rel_path, note.title, sec.heading, sec.content, " ".join(note.tags)),
                )

            # 4. Insert Links
            for target in note.wikilinks:
                conn.execute(
                    """
                    INSERT INTO note_links (source_path, target_title, link_type)
                    VALUES (?, ?, 'wikilink');
                    """,
                    (note.rel_path, target),
                )

            # 5. Insert Tasks
            for t in note.tasks:
                conn.execute(
                    """
                    INSERT INTO tasks (note_path, line_num, description, completed, due_date, completed_date, priority, raw_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        note.rel_path,
                        t.line_num,
                        t.description,
                        1 if t.completed else 0,
                        t.due_date,
                        t.completed_date,
                        t.priority,
                        t.raw_text,
                    ),
                )

    def delete_note(self, rel_path: str) -> None:
        """Remove a note and its cascaded metadata."""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM notes_fts WHERE note_path = ?;", (rel_path,))
            conn.execute("DELETE FROM notes WHERE path = ?;", (rel_path,))

    def search_fts(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search full-text index using SQLite FTS5 with BM25 ranking."""
        # Sanitize query for FTS5 (avoid syntax errors with unmatched quotes/brackets)
        clean_tokens = [t for t in query.replace('"', "").replace("'", "").split() if t.isalnum()]
        if not clean_tokens:
            return []

        fts_query = " OR ".join(f'"{token}"*' for token in clean_tokens)

        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT 
                    note_path,
                    title,
                    heading,
                    content,
                    tags,
                    bm25(notes_fts) as rank,
                    snippet(notes_fts, 3, '[MATCH]', '[/MATCH]', '...', 15) as snippet
                FROM notes_fts
                WHERE notes_fts MATCH ?
                ORDER BY rank
                LIMIT ?;
                """,
                (fts_query, limit),
            )
            return [dict(row) for row in cursor]

    def get_tasks(
        self,
        completed: bool | None = None,
        search: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Query tasks with status and description filters."""
        sql = "SELECT id, note_path, line_num, description, completed, due_date, completed_date, priority, raw_text FROM tasks WHERE 1=1"
        params: list[Any] = []

        if completed is not None:
            sql += " AND completed = ?"
            params.append(1 if completed else 0)

        if search:
            sql += " AND description LIKE ?"
            params.append(f"%{search}%")

        sql += " ORDER BY completed ASC, due_date ASC, id DESC LIMIT ?"
        params.append(limit)

        with self.get_connection() as conn:
            cursor = conn.execute(sql, params)
            return [dict(row) for row in cursor]

    def get_links_from(self, rel_path: str) -> list[str]:
        """Get outgoing links from a note."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT target_title FROM note_links WHERE source_path = ?;", (rel_path,)
            )
            return [row["target_title"] for row in cursor]

    def get_backlinks_to(self, note_title: str) -> list[str]:
        """Get incoming backlinks pointing to a note title."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT source_path FROM note_links WHERE target_title = ?;", (note_title,)
            )
            return [row["source_path"] for row in cursor]

    def get_stats(self) -> dict[str, int]:
        """Return system inventory metrics."""
        with self.get_connection() as conn:
            total_notes = conn.execute("SELECT COUNT(*) FROM notes;").fetchone()[0]
            total_sections = conn.execute("SELECT COUNT(*) FROM note_sections;").fetchone()[0]
            total_tasks = conn.execute("SELECT COUNT(*) FROM tasks;").fetchone()[0]
            completed_tasks = conn.execute(
                "SELECT COUNT(*) FROM tasks WHERE completed = 1;"
            ).fetchone()[0]
            pending_tasks = total_tasks - completed_tasks
            total_links = conn.execute("SELECT COUNT(*) FROM note_links;").fetchone()[0]

            return {
                "total_notes": total_notes,
                "total_sections": total_sections,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "pending_tasks": pending_tasks,
                "total_links": total_links,
            }
