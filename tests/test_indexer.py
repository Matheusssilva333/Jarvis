"""Unit tests for incremental indexer."""
import pytest
from app.knowledge.indexer import VaultIndexer
from app.knowledge.storage import KnowledgeStorage


@pytest.fixture
def mock_vault(tmp_path):
    vault = tmp_path / "mock_vault"
    vault.mkdir()
    (vault / "note1.md").write_text("# Nota Um\nConteúdo sobre automação.", encoding="utf-8")
    (vault / "note2.md").write_text("# Nota Dois\nConteúdo sobre redes.", encoding="utf-8")
    return vault


def test_indexer_incremental_behavior(tmp_path, mock_vault):
    db_file = tmp_path / "test_indexer.db"
    storage = KnowledgeStorage(db_path=db_file)
    indexer = VaultIndexer(vault_path=mock_vault, storage=storage)

    # Initial scan
    rep1 = indexer.scan_vault()
    assert rep1.total_scanned == 2
    assert rep1.added == 2
    assert rep1.unchanged == 0

    # Second scan (zero changes)
    rep2 = indexer.scan_vault()
    assert rep2.total_scanned == 2
    assert rep2.added == 0
    assert rep2.unchanged == 2

    # Add a 3rd note
    (mock_vault / "note3.md").write_text("# Nota Tres\nNovo arquivo.", encoding="utf-8")
    rep3 = indexer.scan_vault()
    assert rep3.added == 1
    assert rep3.unchanged == 2
