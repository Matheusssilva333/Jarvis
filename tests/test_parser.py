"""Unit tests for Obsidian note parsing."""
from app.knowledge.parser import NoteParser


def test_parse_frontmatter_and_tags():
    parser = NoteParser()
    sample = """---
type: project
tags:
  - projeto/carreira
  - Petrobras
status: active
---

# Projeto Industrial

Conteúdo do projeto com tag inline #manutenção.
"""
    note = parser.parse_content(sample, "test/sample.md")
    assert note.title == "Projeto Industrial"
    assert note.note_type == "project"
    assert "projeto/carreira" in note.tags
    assert "Petrobras" in note.tags
    assert "manutenção" in note.tags
    assert len(note.sections) >= 1


def test_parse_tasks():
    parser = NoteParser()
    sample = """
## Tarefas
- [ ] Revisar desenho isométrico 📅 2026-08-15 ⏫
- [x] Concluir relatório de campo ✅ 2026-08-10
"""
    note = parser.parse_content(sample, "test/tasks.md")
    assert len(note.tasks) == 2

    task1 = note.tasks[0]
    assert task1.completed is False
    assert task1.description == "Revisar desenho isométrico"
    assert task1.due_date == "2026-08-15"
    assert task1.priority == "high"

    task2 = note.tasks[1]
    assert task2.completed is True
    assert task2.description == "Concluir relatório de campo"
    assert task2.completed_date == "2026-08-10"


def test_parse_wikilinks():
    parser = NoteParser()
    sample = """
Verifique as notas [[Permutadores]] e também [[Gaxetas|Guia de Gaxetas]].
"""
    note = parser.parse_content(sample, "test/links.md")
    assert "Permutadores" in note.wikilinks
    assert "Gaxetas" in note.wikilinks
