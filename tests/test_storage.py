"""Unit tests for SQLite storage and FTS5 search."""
import pytest
from app.knowledge.parser import NoteParser
from app.knowledge.storage import KnowledgeStorage


@pytest.fixture
def storage(tmp_path):
    db_file = tmp_path / "test_jarvis.db"
    return KnowledgeStorage(db_path=db_file)


def test_storage_save_and_fts_search(storage):
    parser = NoteParser()
    note_content = """# Permutadores Industriais
Os permutadores de calor na UGAV necessitam de inspeção periódica conforme NR-13.
- [ ] Inspecionar feixe tubular
"""
    parsed = parser.parse_content(note_content, "01 Equipamentos/Permutadores.md")
    storage.save_note(parsed)

    results = storage.search_fts("UGAV")
    assert len(results) == 1
    assert results[0]["title"] == "Permutadores Industriais"

    tasks = storage.get_tasks(completed=False)
    assert len(tasks) == 1
    assert "Inspecionar feixe tubular" in tasks[0]["description"]


def test_storage_links_and_backlinks(storage):
    parser = NoteParser()
    note_a = parser.parse_content("Conecta a [[Permutadores]] e [[Gaxetas]]", "MOC.md")
    storage.save_note(note_a)

    backlinks = storage.get_backlinks_to("Permutadores")
    assert "MOC.md" in backlinks
