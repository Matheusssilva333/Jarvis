"""Unit tests for SAO System gamification."""
import pytest
from app.knowledge.parser import NoteParser
from app.knowledge.storage import KnowledgeStorage
from app.sao.manager import SAOSystemManager


@pytest.fixture
def sao_manager(tmp_path):
    db_file = tmp_path / "sao_test.db"
    storage = KnowledgeStorage(db_path=db_file)
    return SAOSystemManager(storage=storage)


def test_sao_initial_stats(sao_manager):
    stats = sao_manager.get_stats()
    assert stats.name == "Matheus Silva"
    assert stats.level >= 1
    assert "Rank" in stats.rank


def test_sao_process_daily_xp(sao_manager, tmp_path):
    parser = NoteParser()
    sample = """# Diário de Teste
- [x] Concluir revisão técnica ✅ 2026-10-06
- [x] Oração matinal ✅ 2026-10-06
"""
    parsed = parser.parse_content(sample, "01 Diário/Teste.md")
    sao_manager.storage.save_note(parsed)

    res = sao_manager.process_daily(date_str="2026-10-06")
    assert res["tasks_count"] == 2
    assert res["xp_earned"] == 20
    assert res["total_xp"] >= 20
