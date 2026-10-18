"""Unit tests for JARVIS Query Engine with Mock and Vault integration."""
import pytest
from app.core.engine import JarvisEngine
from app.knowledge.parser import NoteParser
from app.knowledge.retriever import KnowledgeRetriever
from app.knowledge.storage import KnowledgeStorage
from app.memory.manager import ConversationMemory
from app.providers.mock_provider import MockProvider


@pytest.fixture
def engine_with_mock(tmp_path):
    db_file = tmp_path / "engine_test.db"
    storage = KnowledgeStorage(db_path=db_file)

    # Insert a sample note
    parser = NoteParser()
    sample = """---
type: project
---
# Missão Parada Petrobras
Preparação técnica rigorosa para a parada de manutenção na UT2.
- [ ] Revisar normas NR-13
"""
    parsed = parser.parse_content(sample, "02 Projetos/Petrobras.md")
    storage.save_note(parsed)

    retriever = KnowledgeRetriever(storage=storage)
    provider = MockProvider(response_text="Com base em [[Petrobras]], você deve revisar as normas NR-13.")
    memory = ConversationMemory()

    return JarvisEngine(provider=provider, retriever=retriever, memory=memory)


def test_engine_processes_query_with_sources(engine_with_mock):
    res = engine_with_mock.process("O que preciso fazer para a Petrobras?")
    assert "Com base em [[Petrobras]]" in res.reply
    assert len(res.sources) >= 1
    assert "02 Projetos/Petrobras.md" in res.sources[0]


def test_engine_pending_tasks_direct(engine_with_mock):
    res = engine_with_mock.process("quais são minhas tarefas pendentes?")
    assert "TAREFAS PENDENTES" in res.reply
    assert "Revisar normas NR-13" in res.reply
    assert res.provider == "sqlite"


def test_engine_system_stats_direct(engine_with_mock):
    res = engine_with_mock.process("status do sistema")
    assert "STATUS DO SISTEMA SENTINELA" in res.reply
    assert "**Notas Mapeadas:** 1" in res.reply
