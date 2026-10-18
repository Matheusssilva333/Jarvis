"""Unit tests for LLM providers."""
from app.providers.base import ChatMessage
from app.providers.factory import get_llm_provider
from app.providers.mock_provider import MockProvider


def test_mock_provider():
    prov = MockProvider(response_text="Resposta de teste")
    assert prov.is_available() is True

    res = prov.generate([ChatMessage(role="user", content="Olá")])
    assert res.content == "Resposta de teste"
    assert res.provider == "mock"


def test_provider_factory_fallback():
    # When no keys are provided, factory should safely return MockProvider or Ollama
    prov = get_llm_provider("non_existent_provider")
    assert prov is not None
