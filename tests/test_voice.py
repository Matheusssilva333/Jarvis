"""Unit tests for voice interface."""
from app.voice.stt import MockSTT


def test_mock_stt():
    stt = MockSTT()
    text = stt.transcribe("dummy.wav")
    assert "Jarvis" in text
