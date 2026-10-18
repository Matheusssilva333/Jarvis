"""Unit tests for Supabase pgvector sync and embeddings."""
import pytest
from app.knowledge.supabase_sync import EmbeddingGenerator, VaultKnowledgeSynchronizer


def test_embedding_generator_deterministic():
    embedder = EmbeddingGenerator(dimension=768)
    vec = embedder.generate("Teste de embedding para o Segundo Cérebro do Sentinela")
    assert len(vec) == 768
    # Test normalization: magnitude should be approximately 1.0
    norm = sum(x * x for x in vec) ** 0.5
    assert abs(norm - 1.0) < 1e-4


def test_vault_knowledge_synchronizer_chunking(tmp_path):
    # Criar nota markdown fictícia com seções
    note_file = tmp_path / "Nota_Teste.md"
    content = """# Título da Nota

Esta é a introdução com contexto.

## Seção de Engenharia
Aqui tratamos de arquitetura e rigor industrial no pipeline de dados.

### Subseção de Embeddings
Embeddings transformam texto em representações matemáticas vetoriais.
"""
    note_file.write_text(content, encoding="utf-8")

    sync = VaultKnowledgeSynchronizer(vault_path=tmp_path)
    chunks = sync.scan_and_chunk_vault()
    assert len(chunks) >= 2
    assert any(c.heading == "Seção de Engenharia" for c in chunks)
    assert any(c.heading == "Subseção de Embeddings" for c in chunks)
    assert all(c.word_count > 0 for c in chunks)
    assert all(len(c.content_hash) == 64 for c in chunks)


def test_semantic_search_fallback(tmp_path):
    note_file = tmp_path / "Petrobras.md"
    note_file.write_text(
        "# Meta Petrobras\n\nConquista da grande indústria com soberania e engenharia de dados de elite.",
        encoding="utf-8",
    )

    sync = VaultKnowledgeSynchronizer(vault_path=tmp_path)
    results = sync.semantic_search("Petrobras")
    assert len(results) > 0
    assert "Petrobras" in results[0]["note_title"]
