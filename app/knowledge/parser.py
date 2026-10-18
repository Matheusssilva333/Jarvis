"""Markdown and Obsidian Vault Parser with high fidelity."""
from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ParsedTask:
    line_num: int
    description: str
    completed: bool
    due_date: str | None = None
    completed_date: str | None = None
    priority: str | None = None
    raw_text: str = ""


@dataclass
class ParsedSection:
    heading: str
    level: int
    content: str

    @property
    def token_estimate(self) -> int:
        return len(self.content) // 4


@dataclass
class ParsedNote:
    rel_path: str
    title: str
    content: str
    frontmatter: dict[str, Any]
    tags: list[str]
    wikilinks: list[str]
    sections: list[ParsedSection]
    tasks: list[ParsedTask]
    sha256: str
    mtime: float
    word_count: int
    note_type: str = "general"


class NoteParser:
    """Parses Obsidian Markdown files into structured entities."""

    FRONTMATTER_REGEX = re.compile(r"^---\r?\n(.*?)\r?\n---", re.DOTALL)
    WIKILINK_REGEX = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|([^\]]+))?\]\]")
    INLINE_TAG_REGEX = re.compile(r"(?:^|\s)#([\w\-\/]+)")
    TASK_REGEX = re.compile(r"^\s*-\s*\[([ xX])\]\s*(.*)$")
    HEADING_REGEX = re.compile(r"^(#{1,6})\s+(.*)$")

    DATE_COMPLETED_REGEX = re.compile(r"✅\s*(\d{4}-\d{2}-\d{2})")
    DATE_DUE_REGEX = re.compile(r"📅\s*(\d{4}-\d{2}-\d{2})")
    PRIORITY_HIGH_REGEX = re.compile(r"[⏫🔺]")
    PRIORITY_LOW_REGEX = re.compile(r"[🔽🔻]")

    def parse_file(self, full_path: Path, vault_root: Path) -> ParsedNote:
        """Parse a markdown note from disk."""
        rel_path = os.path.relpath(full_path, vault_root).replace("\\", "/")
        mtime = os.path.getmtime(full_path)

        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        return self.parse_content(content=content, rel_path=rel_path, mtime=mtime)

    def parse_content(self, content: str, rel_path: str, mtime: float = 0.0) -> ParsedNote:
        """Parse note content string into structured fields."""
        sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
        word_count = len(content.split())

        # 1. Frontmatter
        frontmatter: dict[str, Any] = {}
        body = content
        fm_match = self.FRONTMATTER_REGEX.match(content)
        if fm_match:
            raw_fm = fm_match.group(1)
            body = content[fm_match.end():]
            try:
                loaded = yaml.safe_load(raw_fm)
                if isinstance(loaded, dict):
                    frontmatter = loaded
            except Exception:
                # Fallback for malformed frontmatter lines like '{ date }:'
                for line in raw_fm.splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        frontmatter[k.strip()] = v.strip()

        # 2. Note Type
        note_type = str(frontmatter.get("type", "general")).lower()

        # 3. Tags
        tags_set: set[str] = set()
        # Frontmatter tags
        fm_tags = frontmatter.get("tags") or frontmatter.get("tag")
        if isinstance(fm_tags, list):
            for t in fm_tags:
                if t:
                    tags_set.add(str(t).lstrip("#").strip())
        elif isinstance(fm_tags, str):
            for t in fm_tags.split(","):
                t = t.strip().strip("[]'\"")
                if t:
                    tags_set.add(t.lstrip("#"))

        # Inline tags from body (avoiding headings)
        for line in body.splitlines():
            if not line.strip().startswith("#"):
                for t in self.INLINE_TAG_REGEX.findall(line):
                    tags_set.add(t)

        tags = sorted(list(tags_set))

        # 4. Wikilinks
        wikilinks_set: set[str] = set()
        for match in self.WIKILINK_REGEX.finditer(content):
            target = match.group(1).strip()
            if target:
                wikilinks_set.add(target)
        wikilinks = sorted(list(wikilinks_set))

        # 5. Title Resolution
        title = ""
        if "title" in frontmatter and frontmatter["title"]:
            title = str(frontmatter["title"]).strip()
        else:
            # Check first H1 in body
            for line in body.splitlines():
                h_match = self.HEADING_REGEX.match(line.strip())
                if h_match and len(h_match.group(1)) == 1:
                    title = h_match.group(2).strip()
                    break

        if not title:
            # Default to file stem
            title = Path(rel_path).stem

        # 6. Tasks Extraction
        tasks: list[ParsedTask] = []
        for line_idx, line in enumerate(content.splitlines(), start=1):
            t_match = self.TASK_REGEX.match(line)
            if t_match:
                status_char = t_match.group(1)
                completed = status_char.lower() == "x"
                raw_desc = t_match.group(2).strip()

                completed_date: str | None = None
                due_date: str | None = None
                priority: str | None = None

                comp_match = self.DATE_COMPLETED_REGEX.search(raw_desc)
                if comp_match:
                    completed_date = comp_match.group(1)

                due_match = self.DATE_DUE_REGEX.search(raw_desc)
                if due_match:
                    due_date = due_match.group(1)

                if self.PRIORITY_HIGH_REGEX.search(raw_desc):
                    priority = "high"
                elif self.PRIORITY_LOW_REGEX.search(raw_desc):
                    priority = "low"

                # Clean description (remove metadata markers)
                clean_desc = self.DATE_COMPLETED_REGEX.sub("", raw_desc)
                clean_desc = self.DATE_DUE_REGEX.sub("", clean_desc)
                clean_desc = self.PRIORITY_HIGH_REGEX.sub("", clean_desc)
                clean_desc = self.PRIORITY_LOW_REGEX.sub("", clean_desc)
                clean_desc = clean_desc.strip()

                tasks.append(
                    ParsedTask(
                        line_num=line_idx,
                        description=clean_desc,
                        completed=completed,
                        due_date=due_date,
                        completed_date=completed_date,
                        priority=priority,
                        raw_text=line.strip(),
                    )
                )

        # 7. Sections / Headings Chunking
        sections: list[ParsedSection] = []
        current_heading = "Introdução"
        current_level = 1
        current_lines: list[str] = []

        for line in body.splitlines():
            h_match = self.HEADING_REGEX.match(line)
            if h_match:
                # Flush previous section
                sec_text = "\n".join(current_lines).strip()
                if sec_text:
                    sections.append(
                        ParsedSection(
                            heading=current_heading,
                            level=current_level,
                            content=sec_text,
                        )
                    )
                current_level = len(h_match.group(1))
                current_heading = h_match.group(2).strip()
                current_lines = []
            else:
                current_lines.append(line)

        # Flush final section
        sec_text = "\n".join(current_lines).strip()
        if sec_text:
            sections.append(
                ParsedSection(
                    heading=current_heading,
                    level=current_level,
                    content=sec_text,
                )
            )

        # Fallback if no headings existed
        if not sections and body.strip():
            sections.append(
                ParsedSection(
                    heading="Conteúdo",
                    level=1,
                    content=body.strip(),
                )
            )

        return ParsedNote(
            rel_path=rel_path,
            title=title,
            content=content,
            frontmatter=frontmatter,
            tags=tags,
            wikilinks=wikilinks,
            sections=sections,
            tasks=tasks,
            sha256=sha256,
            mtime=mtime,
            word_count=word_count,
            note_type=note_type,
        )
