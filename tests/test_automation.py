"""Unit tests for personal automations and gap detection."""
import pytest
from app.automation.routines import AutomationRoutines
from app.knowledge.parser import NoteParser
from app.knowledge.storage import KnowledgeStorage


@pytest.fixture
def automation(tmp_path):
    db_file = tmp_path / "auto_test.db"
    storage = KnowledgeStorage(db_path=db_file)
    parser = NoteParser()
    sample = """# Projeto Alpha
Nota com link para [[NotaInexistente]] e [[OutraNota]].
"""
    parsed = parser.parse_content(sample, "Projeto.md")
    storage.save_note(parsed)
    return AutomationRoutines(storage=storage)


def test_gap_detection(automation):
    gaps = automation.find_knowledge_gaps()
    assert len(gaps) >= 1
    titles = [g["target_title"] for g in gaps]
    assert "NotaInexistente" in titles


def test_daily_review(automation):
    review = automation.run_daily_review()
    assert "date" in review
    assert "level" in review
    assert "rank" in review
