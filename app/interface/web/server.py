"""FastAPI Local Web Server and Executive SAO System v2.0 Dashboard for JARVIS."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.core.config import settings
from app.core.engine import JarvisEngine
from app.knowledge.indexer import VaultIndexer
from app.knowledge.storage import KnowledgeStorage
from app.knowledge.supabase_sync import SupabaseVectorClient, VaultKnowledgeSynchronizer
from app.sao.manager import SAOSystemManager
from app.tools.registry import ToolRegistry


app = FastAPI(title="JARVIS — SAO System v2.0", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = JarvisEngine()
storage = KnowledgeStorage()
indexer = VaultIndexer(storage=storage)
sao_manager = SAOSystemManager(storage=storage)
tool_registry = ToolRegistry()
sync_engine = VaultKnowledgeSynchronizer(supabase_client=SupabaseVectorClient())


class ChatRequest(BaseModel):
    message: str


class BattleLogRequest(BaseModel):
    description: str
    xp_earned: int = 15
    category: str = "Vitória Operacional"


class ToolExecutionRequest(BaseModel):
    tool_name: str
    arguments: dict = {}


@app.get("/api/stats")
def get_stats():
    """Returns vault metrics and system status."""
    v_stats = storage.get_stats()
    player = sao_manager.get_stats()
    return {
        "vault": v_stats,
        "player": {
            "name": player.name,
            "title": player.title,
            "rank": player.rank,
            "level": player.level,
            "xp": player.xp,
            "next_level_xp": player.next_level_xp,
            "tasks_lifetime": player.tasks_completed_lifetime,
            "tasks_today": player.tasks_completed_today,
            "last_audit": player.last_audit_date,
        },
        "supabase": {
            "configured": sync_engine.client.is_configured,
            "url": settings.supabase_url,
            "dimension": settings.embedding_dimension,
        },
        "security_level": settings.security_level,
        "provider": settings.default_llm_provider,
    }


@app.get("/api/tasks")
def get_tasks(completed: bool | None = None, limit: int = 50):
    """Retrieve tasks from SQLite."""
    return storage.get_tasks(completed=completed, limit=limit)


@app.get("/api/sao")
def get_sao_stats():
    """Retrieve SAO gamification player stats."""
    return sao_manager.get_stats()


@app.post("/api/sao/audit")
def audit_day():
    """Process today's completed tasks, calculate XP, and sync to Supabase."""
    audit_res = sao_manager.process_daily()
    stats = sao_manager.get_stats()
    if sync_engine.client.is_configured:
        sync_engine.client.sync_player_state(stats)
    return audit_res


@app.get("/api/sao/battle-log")
def get_battle_log():
    """Read recent battle log entries from Registro de Batalha.md or database."""
    log_file = settings.vault_path / "⚔️ Centro de Comando" / "Registro de Batalha.md"
    logs = []
    if log_file.exists():
        text = log_file.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            line_s = line.strip()
            if line_s.startswith("- [x]") or line_s.startswith("- [ ]") or ("|" in line_s and "202" in line_s):
                logs.append(line_s)
    return {"logs": logs[:20]}


@app.post("/api/sao/battle-log")
def add_battle_log(req: BattleLogRequest):
    """Add a new victory entry to Registro de Batalha.md and add XP."""
    log_file = settings.vault_path / "⚔️ Centro de Comando" / "Registro de Batalha.md"
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"- [x] **{req.description}** — *{req.category}* (+{req.xp_earned} XP) — `{today}`\n"

    try:
        if log_file.exists():
            content = log_file.read_text(encoding="utf-8")
            content += f"\n{entry}"
            log_file.write_text(content, encoding="utf-8")
        stats = sao_manager.get_stats()
        stats.xp += req.xp_earned
        stats.level = max(1, (stats.xp // 100) + 1)
        stats.next_level_xp = stats.level * 100
        stats.rank = stats.calculate_rank()
        sao_manager.save_stats(stats)
        if sync_engine.client.is_configured:
            sync_engine.client.sync_player_state(stats)
        return {"success": True, "xp_added": req.xp_earned, "total_xp": stats.xp, "level": stats.level}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/supabase/status")
def supabase_status():
    """Check Supabase pgvector configuration and statistics."""
    configured = sync_engine.client.is_configured
    return {
        "configured": configured,
        "url": settings.supabase_url,
        "dimension": settings.embedding_dimension,
        "provider": settings.embedding_provider,
        "vault_path": str(settings.vault_path),
    }


@app.post("/api/supabase/sync")
def trigger_supabase_sync():
    """Trigger vault parsing, embedding generation, and Supabase upsert."""
    res = sync_engine.sync_to_supabase()
    # Também sincroniza o player state
    stats = sao_manager.get_stats()
    if sync_engine.client.is_configured:
        sync_engine.client.sync_player_state(stats)
    return res


@app.get("/api/supabase/search")
def search_supabase(q: str = Query(..., min_length=2), count: int = 5):
    """Semantic vector search across notes."""
    results = sync_engine.semantic_search(q, count=count)
    return {"query": q, "count": len(results), "results": results}


@app.post("/api/reindex")
def trigger_reindex():
    """Scan and synchronize the vault incrementally."""
    report = indexer.scan_vault()
    return {
        "scanned": report.total_scanned,
        "added": report.added,
        "updated": report.updated,
        "unchanged": report.unchanged,
        "deleted": report.deleted,
        "elapsed_seconds": report.elapsed_seconds,
    }


@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    """Process prompt through central JARVIS engine."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Mensagem vazia.")
    res = engine.process(req.message)
    return {
        "reply": res.reply,
        "sources": res.sources,
        "tasks_retrieved": res.tasks_retrieved,
        "latency_seconds": res.latency_seconds,
        "provider": res.provider,
        "model": res.model,
    }


@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    """Serve the complete state-of-the-art SAO System v2.0 RPG Dashboard."""
    return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SAO SYSTEM v2.0 — Centro de Comando Sentinela</title>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@700&family=JetBrains+Mono:wght@400;600;700&family=Outfit:wght@300;400;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg-base: #06080e;
            --bg-card: rgba(13, 18, 30, 0.75);
            --bg-card-hover: rgba(20, 28, 48, 0.9);
            --border-subtle: rgba(56, 189, 248, 0.16);
            --border-glow: rgba(0, 240, 255, 0.5);
            --accent-cyan: #00f0ff;
            --accent-blue: #3b82f6;
            --accent-gold: #f59e0b;
            --accent-emerald: #10b981;
            --accent-purple: #8b5cf6;
            --accent-crimson: #ef4444;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --radius-md: 12px;
            --radius-lg: 18px;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: 'Outfit', sans-serif;
            background-color: var(--bg-base);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
            position: relative;
        }

        /* Canvas Particle Background */
        #bg-canvas {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 0;
            pointer-events: none;
            opacity: 0.35;
        }

        .app-wrapper {
            position: relative;
            z-index: 10;
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }

        /* Header Navigation */
        header {
            padding: 14px 28px;
            background: rgba(6, 8, 14, 0.85);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border-subtle);
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 50;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .brand-badge {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #00f0ff, #8b5cf6);
            border-radius: 10px;
            display: grid;
            place-items: center;
            font-size: 1.3rem;
            box-shadow: 0 0 20px rgba(0, 240, 255, 0.4);
        }

        .brand-text h1 {
            font-size: 1.15rem;
            font-weight: 800;
            letter-spacing: 1px;
            font-family: 'Cinzel', serif;
            background: linear-gradient(to right, #ffffff, var(--accent-cyan));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .brand-text p {
            font-size: 0.72rem;
            color: var(--text-muted);
            font-family: 'JetBrains Mono', monospace;
        }

        .header-actions {
            display: flex;
            gap: 12px;
            align-items: center;
        }

        .btn-rpg {
            background: rgba(0, 240, 255, 0.08);
            border: 1px solid var(--border-subtle);
            color: var(--text-main);
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 0.82rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .btn-rpg:hover {
            background: rgba(0, 240, 255, 0.2);
            border-color: var(--accent-cyan);
            color: var(--accent-cyan);
            transform: translateY(-1px);
            box-shadow: 0 0 15px rgba(0, 240, 255, 0.3);
        }

        .btn-rpg.primary {
            background: linear-gradient(135deg, rgba(0, 240, 255, 0.25), rgba(59, 130, 246, 0.25));
            border-color: var(--accent-cyan);
            color: var(--accent-cyan);
        }

        .btn-rpg.primary:hover {
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
            color: #050b14;
            box-shadow: 0 0 20px rgba(0, 240, 255, 0.6);
        }

        /* Navigation Tabs */
        .tabs-nav {
            display: flex;
            gap: 8px;
            background: rgba(13, 18, 30, 0.6);
            padding: 4px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.06);
        }

        .tab-btn {
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }

        .tab-btn.active, .tab-btn:hover {
            color: #fff;
            background: rgba(255, 255, 255, 0.08);
        }

        .tab-btn.active {
            color: var(--accent-cyan);
            background: rgba(0, 240, 255, 0.12);
            box-shadow: inset 0 0 10px rgba(0, 240, 255, 0.15);
        }

        /* Main Container */
        main {
            flex: 1;
            padding: 24px 28px;
            max-width: 1800px;
            margin: 0 auto;
            width: 100%;
        }

        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: grid;
        }

        /* Grid Layouts */
        .dashboard-grid {
            grid-template-columns: 340px 1fr 380px;
            gap: 24px;
        }

        .quests-grid {
            grid-template-columns: 1fr 380px;
            gap: 24px;
        }

        .brain-grid {
            grid-template-columns: 1fr;
            gap: 24px;
        }

        /* Panels */
        .panel {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-lg);
            backdrop-filter: blur(24px);
            padding: 22px;
            display: flex;
            flex-direction: column;
            gap: 18px;
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
            position: relative;
            overflow: hidden;
        }

        .panel::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, var(--accent-cyan), transparent);
            opacity: 0.3;
        }

        .panel-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            padding-bottom: 14px;
        }

        .panel-title {
            font-size: 0.98rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
            letter-spacing: 0.5px;
        }

        /* Player HUD Profile Card */
        .player-card {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            padding: 12px 0;
            position: relative;
        }

        .avatar-frame {
            width: 88px;
            height: 88px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(0, 240, 255, 0.25) 0%, rgba(13, 18, 30, 0.8) 70%);
            border: 2px solid var(--accent-cyan);
            box-shadow: 0 0 25px rgba(0, 240, 255, 0.4);
            display: grid;
            place-items: center;
            font-size: 2.2rem;
            margin-bottom: 12px;
            position: relative;
        }

        .level-badge {
            position: absolute;
            bottom: -6px;
            background: linear-gradient(135deg, var(--accent-gold), #b45309);
            color: #000;
            font-weight: 800;
            font-size: 0.75rem;
            padding: 2px 10px;
            border-radius: 12px;
            box-shadow: 0 0 10px rgba(245, 158, 11, 0.6);
            font-family: 'JetBrains Mono', monospace;
        }

        .player-name {
            font-size: 1.25rem;
            font-weight: 800;
            margin-top: 6px;
        }

        .player-title {
            font-size: 0.8rem;
            color: var(--accent-cyan);
            font-family: 'JetBrains Mono', monospace;
            margin-bottom: 14px;
        }

        .rank-pill {
            display: inline-block;
            background: rgba(139, 92, 246, 0.15);
            border: 1px solid var(--accent-purple);
            color: #c4b5fd;
            padding: 4px 14px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 700;
            margin-bottom: 16px;
        }

        /* XP Progress Bar */
        .xp-container {
            width: 100%;
            background: rgba(0, 0, 0, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 10px 14px;
        }

        .xp-labels {
            display: flex;
            justify-content: space-between;
            font-size: 0.75rem;
            font-family: 'JetBrains Mono', monospace;
            margin-bottom: 6px;
            color: var(--text-muted);
        }

        .xp-bar-track {
            height: 10px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 6px;
            overflow: hidden;
            position: relative;
        }

        .xp-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--accent-cyan), var(--accent-emerald));
            width: 0%;
            border-radius: 6px;
            box-shadow: 0 0 12px var(--accent-cyan);
            transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
        }

        /* Stats Mini Cards */
        .stats-mini-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            width: 100%;
        }

        .stat-mini-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 10px;
            padding: 12px;
            text-align: left;
        }

        .stat-mini-val {
            font-size: 1.25rem;
            font-weight: 800;
            font-family: 'JetBrains Mono', monospace;
            color: #fff;
        }

        .stat-mini-label {
            font-size: 0.7rem;
            color: var(--text-muted);
            margin-top: 2px;
        }

        /* Chat / Console */
        .chat-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            height: 620px;
        }

        .chat-messages {
            flex: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 14px;
            padding-right: 6px;
        }

        .chat-msg {
            max-width: 85%;
            padding: 12px 18px;
            border-radius: 14px;
            font-size: 0.88rem;
            line-height: 1.5;
            position: relative;
            animation: fadeIn 0.2s ease-in;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .chat-msg.user {
            align-self: flex-end;
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(0, 240, 255, 0.2));
            border: 1px solid rgba(0, 240, 255, 0.4);
            color: #fff;
        }

        .chat-msg.jarvis {
            align-self: flex-start;
            background: rgba(18, 24, 38, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: #e2e8f0;
        }

        .chat-input-bar {
            display: flex;
            gap: 10px;
            margin-top: 14px;
        }

        .chat-input {
            flex: 1;
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid var(--border-subtle);
            border-radius: 10px;
            padding: 12px 16px;
            color: #fff;
            font-family: 'Outfit', sans-serif;
            font-size: 0.9rem;
            outline: none;
            transition: border-color 0.2s;
        }

        .chat-input:focus {
            border-color: var(--accent-cyan);
            box-shadow: 0 0 15px rgba(0, 240, 255, 0.2);
        }

        /* Tasks / Quests list */
        .task-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
            max-height: 520px;
            overflow-y: auto;
        }

        .task-item {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 10px 14px;
            display: flex;
            align-items: flex-start;
            gap: 12px;
            transition: all 0.2s;
        }

        .task-item:hover {
            background: rgba(255, 255, 255, 0.05);
            border-color: var(--border-subtle);
        }

        .task-desc {
            font-size: 0.85rem;
            flex: 1;
        }

        .task-meta {
            font-size: 0.7rem;
            color: var(--text-muted);
            font-family: 'JetBrains Mono', monospace;
            margin-top: 4px;
        }

        /* Search Results in Second Brain */
        .search-card {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            transition: all 0.2s;
        }

        .search-card:hover {
            border-color: var(--accent-cyan);
            background: rgba(0, 240, 255, 0.04);
        }

        .search-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }

        .search-title {
            font-weight: 700;
            color: var(--accent-cyan);
            font-size: 0.95rem;
        }

        .search-sim {
            background: rgba(16, 185, 129, 0.15);
            border: 1px solid var(--accent-emerald);
            color: var(--accent-emerald);
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.72rem;
            font-family: 'JetBrains Mono', monospace;
        }

        .search-body {
            font-size: 0.85rem;
            color: #cbd5e1;
            line-height: 1.5;
            white-space: pre-wrap;
        }

        /* Toast / Notification */
        #toast {
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: rgba(13, 18, 30, 0.95);
            border: 1px solid var(--accent-cyan);
            padding: 12px 20px;
            border-radius: 10px;
            color: #fff;
            font-size: 0.85rem;
            box-shadow: 0 0 25px rgba(0, 240, 255, 0.4);
            transform: translateY(100px);
            opacity: 0;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            z-index: 100;
        }
        #toast.show {
            transform: translateY(0);
            opacity: 1;
        }
    </style>
</head>
<body>
    <canvas id="bg-canvas"></canvas>

    <div class="app-wrapper">
        <header>
            <div class="brand">
                <div class="brand-badge">⚔️</div>
                <div class="brand-text">
                    <h1>SAO SYSTEM v2.0</h1>
                    <p>SENTINELA CORE // SEGUNDO CÉREBRO VETORIAL</p>
                </div>
            </div>

            <div class="tabs-nav">
                <button class="tab-btn active" onclick="switchTab('dashboard')">⚔️ Centro de Comando</button>
                <button class="tab-btn" onclick="switchTab('quests')">🗡️ Masmorras & Quests</button>
                <button class="tab-btn" onclick="switchTab('brain')">🧠 Supabase pgvector</button>
                <button class="tab-btn" onclick="switchTab('battle')">📜 Registro de Batalha</button>
            </div>

            <div class="header-actions">
                <button class="btn-rpg" onclick="auditDay()">⚡ Auditar Dia (+XP)</button>
                <button class="btn-rpg primary" onclick="syncSupabase()">🔗 Sincronizar Supabase</button>
            </div>
        </header>

        <main>
            <!-- ABA 1: CENTRO DE COMANDO -->
            <div id="tab-dashboard" class="tab-content active dashboard-grid">
                <!-- Coluna Esquerda: HUD Jogador -->
                <div class="panel">
                    <div class="panel-header">
                        <div class="panel-title">🛡️ STATUS DO JOGADOR</div>
                        <span id="rank-tag" class="rank-pill">Rank E</span>
                    </div>

                    <div class="player-card">
                        <div class="avatar-frame">
                            👤
                            <div id="player-level" class="level-badge">LVL 1</div>
                        </div>
                        <div id="player-name" class="player-name">Matheus Silva</div>
                        <div id="player-title" class="player-title">Sentinela Atalaia / Engenheiro</div>

                        <div class="xp-container">
                            <div class="xp-labels">
                                <span>EXPERIÊNCIA (XP)</span>
                                <span id="xp-numbers">0 / 100 XP</span>
                            </div>
                            <div class="xp-bar-track">
                                <div id="xp-bar" class="xp-bar-fill"></div>
                            </div>
                        </div>
                    </div>

                    <div class="stats-mini-grid">
                        <div class="stat-mini-card">
                            <div id="stat-tasks-lifetime" class="stat-mini-val">0</div>
                            <div class="stat-mini-label">Missões Históricas</div>
                        </div>
                        <div class="stat-mini-card">
                            <div id="stat-tasks-today" class="stat-mini-val">0</div>
                            <div class="stat-mini-label">Vitórias Hoje</div>
                        </div>
                        <div class="stat-mini-card">
                            <div id="stat-notes-total" class="stat-mini-val">0</div>
                            <div class="stat-mini-label">Notas no Cofre</div>
                        </div>
                        <div class="stat-mini-card">
                            <div id="stat-supabase-status" class="stat-mini-val" style="color:var(--accent-cyan); font-size: 0.9rem;">Pronto</div>
                            <div class="stat-mini-label">Supabase pgvector</div>
                        </div>
                    </div>

                    <div style="margin-top: 10px;">
                        <canvas id="radarChart" height="210"></canvas>
                    </div>
                </div>

                <!-- Coluna Centro: JARVIS Chat Terminal -->
                <div class="panel">
                    <div class="panel-header">
                        <div class="panel-title">🤖 CONSOLE OPERACIONAL JARVIS</div>
                        <span id="llm-provider-badge" style="font-size:0.75rem; color:var(--text-muted); font-family:'JetBrains Mono';">GEMINI // RIGOR INDUSTRIAL</span>
                    </div>

                    <div class="chat-container">
                        <div id="chat-messages" class="chat-messages">
                            <div class="chat-msg jarvis">
                                ⚔️ <strong>Sentinela Core online.</strong> Sistema reestruturado sob o padrão SAO System v2.0.<br>
                                Digite um comando, faça uma pergunta sobre suas notas ou peça uma auditoria de missão.
                            </div>
                        </div>

                        <div class="chat-input-bar">
                            <input id="chat-input" class="chat-input" placeholder="Comande o Sentinela ou pergunte algo ao seu Segundo Cérebro..." onkeydown="if(event.key==='Enter') sendChat()">
                            <button class="btn-rpg primary" onclick="sendChat()">Enviar</button>
                        </div>
                    </div>
                </div>

                <!-- Coluna Direita: Missões Diárias Rápidas -->
                <div class="panel">
                    <div class="panel-header">
                        <div class="panel-title">🗡️ MISSÕES PENDENTES</div>
                        <button class="btn-rpg" onclick="loadTasks()" style="padding:4px 8px; font-size:0.75rem;">🔄</button>
                    </div>

                    <div id="tasks-container" class="task-list">
                        <div style="color:var(--text-muted); font-size:0.85rem; text-align:center; padding: 20px;">Carregando missões...</div>
                    </div>

                    <div style="margin-top:auto; padding-top:14px; border-top:1px solid rgba(255,255,255,0.06);">
                        <button class="btn-rpg primary" style="width:100%; justify-content:center;" onclick="switchTab('quests')">Ver Quadro Completo de Quests →</button>
                    </div>
                </div>
            </div>

            <!-- ABA 2: MASMORRAS & QUESTS -->
            <div id="tab-quests" class="tab-content quests-grid">
                <div class="panel">
                    <div class="panel-header">
                        <div class="panel-title">🗡️ QUADRO DE MASMORRAS & TAREFAS</div>
                        <span style="font-size:0.8rem; color:var(--text-muted);">Sincronizado com Obsidian Vault</span>
                    </div>
                    <div id="all-tasks-container" class="task-list" style="max-height: 640px;"></div>
                </div>

                <div class="panel">
                    <div class="panel-header">
                        <div class="panel-title">🏆 REGRAS DE CONQUISTA DE XP</div>
                    </div>
                    <div style="font-size:0.85rem; line-height:1.6; color:var(--text-muted);">
                        <p><strong style="color:#fff;">• Missão Diária Concluída:</strong> +10 XP</p>
                        <p><strong style="color:#fff;">• Quest Principal Entregue:</strong> +100 a +250 XP</p>
                        <p><strong style="color:#fff;">• Raid Industrial Superada:</strong> +300 a +500 XP</p>
                        <p><strong style="color:#fff;">• Registro de Batalha Auditado:</strong> +15 XP</p>
                        <p><strong style="color:#fff;">• Leitura/Resumo Permanente:</strong> +25 XP</p>
                        <hr style="border-color:rgba(255,255,255,0.08); margin:14px 0;">
                        <p style="color:var(--accent-gold); font-size:0.8rem;">
                            <em>"O Binário do Caráter: Ou há Evidência (XP) ou há Ruído (Falha). Sem prova, o XP é negado."</em>
                        </p>
                    </div>
                </div>
            </div>

            <!-- ABA 3: SEGUNDO CÉREBRO (SUPABASE PGVECTOR) -->
            <div id="tab-brain" class="tab-content brain-grid">
                <div class="panel">
                    <div class="panel-header">
                        <div class="panel-title">🧠 SEGUNDO CÉREBRO VETORIAL — BUSCA SEMÂNTICA SUPABASE</div>
                        <div style="display:flex; gap:10px;">
                            <span id="brain-config-status" class="rank-pill" style="margin:0; background:rgba(0,240,255,0.1); border-color:var(--accent-cyan); color:var(--accent-cyan);">pgvector Ativo</span>
                            <button class="btn-rpg primary" onclick="syncSupabase()">Sincronizar Cofre Agora</button>
                        </div>
                    </div>

                    <div style="display:flex; gap:12px; margin-bottom: 20px;">
                        <input id="brain-search-input" class="chat-input" placeholder="Pesquise por conceito, resumo, nota técnica ou ideia..." onkeydown="if(event.key==='Enter') executeSemanticSearch()">
                        <button class="btn-rpg primary" onclick="executeSemanticSearch()">Buscar no Supabase</button>
                    </div>

                    <div id="brain-results" style="max-height: 520px; overflow-y:auto;">
                        <div style="text-align:center; padding: 40px; color:var(--text-muted);">
                            Digite uma consulta acima para recuperar os trechos de conhecimento do cofre mais relevantes semanticamente via embeddings.
                        </div>
                    </div>
                </div>
            </div>

            <!-- ABA 4: REGISTRO DE BATALHA -->
            <div id="tab-battle" class="tab-content quests-grid">
                <div class="panel">
                    <div class="panel-header">
                        <div class="panel-title">📜 HISTÓRICO DE BATALHAS AUDITADAS</div>
                        <button class="btn-rpg" onclick="loadBattleLog()">🔄 Atualizar</button>
                    </div>
                    <div id="battle-log-container" class="task-list" style="max-height: 600px;"></div>
                </div>

                <div class="panel">
                    <div class="panel-header">
                        <div class="panel-title">⚔️ REGISTRAR NOVA VITÓRIA</div>
                    </div>
                    <div style="display:flex; flex-direction:column; gap:12px;">
                        <label style="font-size:0.8rem; color:var(--text-muted);">Descrição da Vitória / Evidência:</label>
                        <input id="new-victory-desc" class="chat-input" placeholder="Ex: Módulo de sync testado com 99 notas...">

                        <label style="font-size:0.8rem; color:var(--text-muted);">Categoria:</label>
                        <select id="new-victory-cat" class="chat-input" style="background:#0a0f1d;">
                            <option value="Engenharia / Código">Engenharia / Código (+20 XP)</option>
                            <option value="Dados / SQL">Dados / SQL (+20 XP)</option>
                            <option value="Disciplina / Jejum">Disciplina / Jejum (+15 XP)</option>
                            <option value="Carreira / Petrobras">Carreira / Petrobras (+30 XP)</option>
                            <option value="Muralha / Foco">Muralha / Foco (+15 XP)</option>
                        </select>

                        <button class="btn-rpg primary" style="justify-content:center; margin-top:8px;" onclick="submitNewVictory()">Gravar no Registro & Adicionar XP</button>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <div id="toast"></div>

    <script>
        // Particle Canvas
        const canvas = document.getElementById('bg-canvas');
        const ctx = canvas.getContext('2d');
        let particles = [];

        function resizeCanvas() {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }
        window.addEventListener('resize', resizeCanvas);
        resizeCanvas();

        for (let i = 0; i < 45; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                radius: Math.random() * 1.5 + 0.5,
                vx: (Math.random() - 0.5) * 0.4,
                vy: (Math.random() - 0.5) * 0.4,
                alpha: Math.random() * 0.5 + 0.2
            });
        }

        function animateParticles() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = 'rgba(0, 240, 255, 0.6)';
            particles.forEach(p => {
                p.x += p.vx;
                p.y += p.vy;
                if (p.x < 0) p.x = canvas.width;
                if (p.x > canvas.width) p.x = 0;
                if (p.y < 0) p.y = canvas.height;
                if (p.y > canvas.height) p.y = 0;

                ctx.beginPath();
                ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
                ctx.fill();
            });
            requestAnimationFrame(animateParticles);
        }
        animateParticles();

        // Radar Chart (Atributos do Sentinela)
        let radarChart = null;
        function initRadar(level = 1) {
            const ctxR = document.getElementById('radarChart').getContext('2d');
            const dataBase = Math.min(100, 20 + level * 5);
            radarChart = new Chart(ctxR, {
                type: 'radar',
                data: {
                    labels: ['Engenharia', 'Disciplina', 'Espiritual', 'Físico', 'Arquitetura'],
                    datasets: [{
                        label: 'Atributos Sentinela',
                        data: [dataBase + 10, dataBase, dataBase + 5, dataBase - 5, dataBase + 8],
                        backgroundColor: 'rgba(0, 240, 255, 0.2)',
                        borderColor: '#00f0ff',
                        borderWidth: 2,
                        pointBackgroundColor: '#00f0ff',
                    }]
                },
                options: {
                    scales: {
                        r: {
                            angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
                            grid: { color: 'rgba(255, 255, 255, 0.08)' },
                            pointLabels: { color: '#94a3b8', font: { size: 10, family: 'Outfit' } },
                            ticks: { display: false, max: 100, min: 0 }
                        }
                    },
                    plugins: { legend: { display: false } }
                }
            });
        }

        // Tabs
        function switchTab(tabId) {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById(`tab-${tabId}`).classList.add('active');

            if (tabId === 'quests') loadAllTasks();
            if (tabId === 'battle') loadBattleLog();
        }

        function showToast(msg) {
            const toast = document.getElementById('toast');
            toast.innerText = msg;
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 3500);
        }

        // Carregar Estatísticas & Jogador
        async function loadStats() {
            try {
                const res = await fetch('/api/stats');
                const data = await res.json();

                const p = data.player;
                document.getElementById('player-name').innerText = p.name;
                document.getElementById('player-title').innerText = p.title;
                document.getElementById('player-level').innerText = `LVL ${p.level}`;
                document.getElementById('rank-tag').innerText = p.rank;
                document.getElementById('xp-numbers').innerText = `${p.xp} / ${p.next_level_xp} XP`;

                const pct = Math.min(100, Math.round((p.xp / p.next_level_xp) * 100));
                document.getElementById('xp-bar').style.width = `${pct}%`;

                document.getElementById('stat-tasks-lifetime').innerText = p.tasks_lifetime;
                document.getElementById('stat-tasks-today').innerText = p.tasks_today;
                document.getElementById('stat-notes-total').innerText = data.vault.total_notes;

                if (!radarChart) initRadar(p.level);

                if (data.supabase.configured) {
                    document.getElementById('stat-supabase-status').innerText = 'Ativo (pgvector)';
                    document.getElementById('stat-supabase-status').style.color = 'var(--accent-emerald)';
                } else {
                    document.getElementById('stat-supabase-status').innerText = 'Pendente Chave';
                    document.getElementById('stat-supabase-status').style.color = 'var(--accent-gold)';
                }
            } catch (e) {
                console.error(e);
            }
        }

        // Carregar Tarefas / Missões
        async function loadTasks() {
            try {
                const res = await fetch('/api/tasks?limit=6');
                const tasks = await res.json();
                const container = document.getElementById('tasks-container');
                container.innerHTML = '';

                if (tasks.length === 0) {
                    container.innerHTML = '<div style="color:var(--text-muted); padding:20px; text-align:center;">Nenhuma missão pendente no momento.</div>';
                    return;
                }

                tasks.forEach(t => {
                    const item = document.createElement('div');
                    item.className = 'task-item';
                    item.innerHTML = `
                        <input type="checkbox" ${t.completed ? 'checked' : ''} style="margin-top:3px;">
                        <div class="task-desc">
                            <div>${t.description}</div>
                            <div class="task-meta">📂 ${t.note_path}</div>
                        </div>
                    `;
                    container.appendChild(item);
                });
            } catch (e) {
                console.error(e);
            }
        }

        async function loadAllTasks() {
            try {
                const res = await fetch('/api/tasks?limit=50');
                const tasks = await res.json();
                const container = document.getElementById('all-tasks-container');
                container.innerHTML = '';

                tasks.forEach(t => {
                    const item = document.createElement('div');
                    item.className = 'task-item';
                    item.innerHTML = `
                        <input type="checkbox" ${t.completed ? 'checked' : ''} style="margin-top:3px;">
                        <div class="task-desc" style="${t.completed ? 'text-decoration:line-through; opacity:0.6;' : ''}">
                            <div>${t.description}</div>
                            <div class="task-meta">📂 ${t.note_path}</div>
                        </div>
                    `;
                    container.appendChild(item);
                });
            } catch (e) {
                console.error(e);
            }
        }

        // Chat
        async function sendChat() {
            const input = document.getElementById('chat-input');
            const msg = input.value.trim();
            if (!msg) return;

            const box = document.getElementById('chat-messages');

            const uDiv = document.createElement('div');
            uDiv.className = 'chat-msg user';
            uDiv.innerText = msg;
            box.appendChild(uDiv);
            input.value = '';
            box.scrollTop = box.scrollHeight;

            const jDiv = document.createElement('div');
            jDiv.className = 'chat-msg jarvis';
            jDiv.innerText = 'Raciocinando sobre o cofre...';
            box.appendChild(jDiv);
            box.scrollTop = box.scrollHeight;

            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: msg})
                });
                const data = await res.json();
                jDiv.innerHTML = data.reply.replace(/\\n/g, '<br>');
                box.scrollTop = box.scrollHeight;
                loadStats();
            } catch (e) {
                jDiv.innerText = 'Erro operacional ao consultar Sentinela.';
            }
        }

        // Auditar Dia
        async function auditDay() {
            showToast('Auditando missões e processando XP...');
            try {
                const res = await fetch('/api/sao/audit', { method: 'POST' });
                const data = await res.json();
                showToast(`Auditoria Concluída: +${data.xp_earned} XP conquistados! (Nível ${data.level})`);
                loadStats();
                loadTasks();
            } catch (e) {
                showToast('Erro ao auditar tarefas.');
            }
        }

        // Sincronizar Supabase
        async function syncSupabase() {
            showToast('Iniciando sincronização com Supabase pgvector...');
            try {
                const res = await fetch('/api/supabase/sync', { method: 'POST' });
                const data = await res.json();
                if (data.success) {
                    showToast(`Supabase atualizado! ${data.chunks_upserted} chunks sincronizados em ${data.elapsed_seconds}s.`);
                } else {
                    showToast(data.message || `Status: ${data.notes_count} notas preparadas para envio.`);
                }
                loadStats();
            } catch (e) {
                showToast('Erro ao sincronizar com Supabase.');
            }
        }

        // Busca Semântica
        async function executeSemanticSearch() {
            const q = document.getElementById('brain-search-input').value.trim();
            if (!q) return;

            const resBox = document.getElementById('brain-results');
            resBox.innerHTML = '<div style="text-align:center; padding:30px; color:var(--accent-cyan);">Calculando similaridade por cosseno...</div>';

            try {
                const res = await fetch(`/api/supabase/search?q=${encodeURIComponent(q)}&count=5`);
                const data = await res.json();
                resBox.innerHTML = '';

                if (!data.results || data.results.length === 0) {
                    resBox.innerHTML = '<div style="text-align:center; padding:30px; color:var(--text-muted);">Nenhum trecho com similaridade suficiente foi encontrado.</div>';
                    return;
                }

                data.results.forEach(r => {
                    const card = document.createElement('div');
                    card.className = 'search-card';
                    const simPct = r.similarity ? Math.round(r.similarity * 100) : 85;
                    card.innerHTML = `
                        <div class="search-header">
                            <div class="search-title">📄 ${r.note_title} // ${r.heading || 'Geral'}</div>
                            <span class="search-sim">${simPct}% Match</span>
                        </div>
                        <div class="search-body">${r.content}</div>
                        <div class="task-meta" style="margin-top:8px;">Caminho: ${r.note_path}</div>
                    `;
                    resBox.appendChild(card);
                });
            } catch (e) {
                resBox.innerHTML = '<div style="text-align:center; padding:30px; color:var(--accent-crimson);">Erro ao consultar base vetorial.</div>';
            }
        }

        // Battle Log
        async function loadBattleLog() {
            try {
                const res = await fetch('/api/sao/battle-log');
                const data = await res.json();
                const container = document.getElementById('battle-log-container');
                container.innerHTML = '';

                if (!data.logs || data.logs.length === 0) {
                    container.innerHTML = '<div style="color:var(--text-muted); padding:20px; text-align:center;">Nenhum registro de batalha recente encontrado.</div>';
                    return;
                }

                data.logs.forEach(l => {
                    const item = document.createElement('div');
                    item.className = 'task-item';
                    item.innerHTML = `<div class="task-desc" style="color:#e2e8f0;">${l}</div>`;
                    container.appendChild(item);
                });
            } catch (e) {
                console.error(e);
            }
        }

        async function submitNewVictory() {
            const desc = document.getElementById('new-victory-desc').value.trim();
            const cat = document.getElementById('new-victory-cat').value;
            if (!desc) {
                showToast('Informe a descrição da vitória.');
                return;
            }

            const xp = cat.includes('+30') ? 30 : (cat.includes('+20') ? 20 : 15);

            try {
                const res = await fetch('/api/sao/battle-log', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({description: desc, category: cat, xp_earned: xp})
                });
                const data = await res.json();
                showToast(`Vitória Registrada! +${data.xp_added} XP conquistados.`);
                document.getElementById('new-victory-desc').value = '';
                loadStats();
                loadBattleLog();
            } catch (e) {
                showToast('Erro ao registrar vitória.');
            }
        }

        loadStats();
        loadTasks();
    </script>
</body>
</html>
"""


def start_server(host: str | None = None, port: int | None = None):
    """Launch the JARVIS local/cloud server."""
    import os
    h = host or os.getenv("HOST", "0.0.0.0")
    p = port or int(os.getenv("PORT", "8080"))
    uvicorn.run("app.interface.web.server:app", host=h, port=p, reload=False)


if __name__ == "__main__":
    start_server()
