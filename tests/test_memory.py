"""Unit tests for conversation memory."""
from app.memory.manager import ConversationMemory


def test_memory_sliding_window():
    memory = ConversationMemory(max_history_turns=2)
    # Add 3 turns
    for i in range(3):
        memory.add_user_message(f"Pergunta {i}")
        memory.add_assistant_message(f"Resposta {i}")

    # Should keep only 2 turns (4 messages)
    assert len(memory.messages) == 4
    assert memory.messages[0].content == "Pergunta 1"
    assert memory.messages[-1].content == "Resposta 2"


def test_memory_export_markdown():
    memory = ConversationMemory()
    memory.add_user_message("O que é um permutador?")
    memory.add_assistant_message("É um trocador de calor.")
    md = memory.export_as_markdown(title="Teste")

    assert "# 💬 Teste" in md
    assert "Matheus" in md
    assert "JARVIS" in md
    assert "trocador de calor" in md
