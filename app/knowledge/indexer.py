"""Incremental vault indexer and file synchronizer."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path

from app.core.config import logger, settings
from app.knowledge.parser import NoteParser
from app.knowledge.storage import KnowledgeStorage


@dataclass
class IndexReport:
    total_scanned: int = 0
    added: int = 0
    updated: int = 0
    deleted: int = 0
    unchanged: int = 0
    elapsed_seconds: float = 0.0
    errors: list[str] = field(default_factory=list)


class VaultIndexer:
    """Performs fast incremental scanning and indexing of the Obsidian Vault."""

    IGNORED_DIRS = {
        ".obsidian",
        ".claude",
        ".claudian",
        ".vscode",
        ".git",
        "jarvis",
        "node_modules",
        "__pycache__",
    }

    def __init__(
        self,
        vault_path: Path | None = None,
        storage: KnowledgeStorage | None = None,
        parser: NoteParser | None = None,
    ):
        self.vault_path = vault_path or settings.vault_path
        self.storage = storage or KnowledgeStorage()
        self.parser = parser or NoteParser()

    def scan_vault(self, force: bool = False) -> IndexReport:
        """Scan the vault and incrementally synchronize with SQLite FTS."""
        start_time = time.time()
        report = IndexReport()

        if not self.vault_path.exists():
            msg = f"Vault path does not exist: {self.vault_path}"
            logger.error(msg)
            report.errors.append(msg)
            return report

        existing_db_map = {} if force else self.storage.get_indexed_notes_map()
        discovered_paths: set[str] = set()

        logger.info(f"Starting incremental vault scan on: {self.vault_path}")

        for root, dirs, files in os.walk(self.vault_path):
            # Prune ignored directories in-place
            dirs[:] = [d for d in dirs if d not in self.IGNORED_DIRS and not d.startswith(".")]

            for file in files:
                if not file.endswith(".md"):
                    continue

                full_path = Path(root) / file
                rel_path = os.path.relpath(full_path, self.vault_path).replace("\\", "/")
                discovered_paths.add(rel_path)
                report.total_scanned += 1

                try:
                    current_mtime = os.path.getmtime(full_path)

                    if rel_path in existing_db_map:
                        cached_mtime, cached_sha = existing_db_map[rel_path]
                        # Quick mtime check
                        if abs(current_mtime - cached_mtime) < 0.001 and not force:
                            report.unchanged += 1
                            continue

                        # Read & check sha256 to avoid re-indexing unchanged content
                        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                            content = f.read()

                        parsed = self.parser.parse_content(content, rel_path, current_mtime)
                        if parsed.sha256 == cached_sha and not force:
                            report.unchanged += 1
                            continue

                        # Truly modified
                        self.storage.save_note(parsed)
                        report.updated += 1
                        logger.debug(f"Updated note: {rel_path}")
                    else:
                        # New note
                        parsed = self.parser.parse_file(full_path, self.vault_path)
                        self.storage.save_note(parsed)
                        report.added += 1
                        logger.debug(f"Added note: {rel_path}")

                except Exception as e:
                    err_msg = f"Error indexing {rel_path}: {e}"
                    logger.error(err_msg)
                    report.errors.append(err_msg)

        # Detect deleted files (were in DB but no longer on disk)
        for db_path in existing_db_map:
            if db_path not in discovered_paths:
                self.storage.delete_note(db_path)
                report.deleted += 1
                logger.debug(f"Deleted note from index: {db_path}")

        report.elapsed_seconds = round(time.time() - start_time, 3)
        logger.info(
            f"Scan finished in {report.elapsed_seconds}s. Scanned: {report.total_scanned}, "
            f"Added: {report.added}, Updated: {report.updated}, "
            f"Deleted: {report.deleted}, Unchanged: {report.unchanged}."
        )
        return report
