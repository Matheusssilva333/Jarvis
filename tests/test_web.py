"""Integration tests for JARVIS FastAPI Web Endpoints."""
from fastapi.testclient import TestClient
from app.interface.web.server import app

client = TestClient(app)


def test_web_stats_endpoint():
    res = client.get("/api/stats")
    assert res.status_code == 200
    data = res.json()
    assert "vault" in data
    assert "player" in data
    assert data["vault"]["total_notes"] >= 0


def test_web_tasks_endpoint():
    res = client.get("/api/tasks")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_web_chat_endpoint():
    res = client.post("/api/chat", json={"message": "status do sistema"})
    assert res.status_code == 200
    data = res.json()
    assert "reply" in data
    assert "STATUS DO SISTEMA SENTINELA" in data["reply"]


def test_web_reindex_endpoint():
    res = client.post("/api/reindex")
    assert res.status_code == 200
    data = res.json()
    assert "scanned" in data
