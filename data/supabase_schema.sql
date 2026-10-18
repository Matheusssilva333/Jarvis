-- ==============================================================================
-- SAO SYSTEM v2.0 — SUPABASE PGVECTOR SCHEMA
-- Projeto: etztvnzxkhdoqwswajgb (sa-east-1)
-- Executar no SQL Editor do Supabase Dashboard:
-- https://supabase.com/dashboard/project/etztvnzxkhdoqwswajgb/sql
-- ==============================================================================

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    note_path TEXT NOT NULL,
    note_title TEXT NOT NULL,
    heading TEXT,
    content TEXT NOT NULL,
    tags TEXT[] DEFAULT '{}',
    chunk_index INTEGER DEFAULT 0,
    word_count INTEGER DEFAULT 0,
    embedding vector(768),
    content_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(note_path, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_kc_note_path ON knowledge_chunks(note_path);
CREATE INDEX IF NOT EXISTS idx_kc_content_hash ON knowledge_chunks(content_hash);

CREATE INDEX IF NOT EXISTS idx_kc_embedding_hnsw 
    ON knowledge_chunks 
    USING hnsw (embedding vector_cosine_ops);

CREATE OR REPLACE FUNCTION match_knowledge(
    query_embedding vector(768),
    match_threshold FLOAT DEFAULT 0.5,
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    note_path TEXT,
    note_title TEXT,
    heading TEXT,
    content TEXT,
    tags TEXT[],
    similarity FLOAT
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT
        kc.id,
        kc.note_path,
        kc.note_title,
        kc.heading,
        kc.content,
        kc.tags,
        (1 - (kc.embedding <=> query_embedding))::FLOAT AS similarity
    FROM knowledge_chunks kc
    WHERE kc.embedding IS NOT NULL 
      AND (1 - (kc.embedding <=> query_embedding)) >= match_threshold
    ORDER BY kc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

CREATE TABLE IF NOT EXISTS vault_sync_log (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sync_type TEXT NOT NULL DEFAULT 'incremental',
    notes_added INT DEFAULT 0,
    notes_updated INT DEFAULT 0,
    notes_deleted INT DEFAULT 0,
    chunks_total INT DEFAULT 0,
    elapsed_seconds FLOAT DEFAULT 0.0,
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT DEFAULT 'success',
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS rpg_player_state (
    id INT PRIMARY KEY DEFAULT 1,
    player_name TEXT NOT NULL DEFAULT 'Matheus Silva',
    title TEXT NOT NULL DEFAULT 'Sentinela Atalaia / Engenheiro',
    rank TEXT NOT NULL DEFAULT 'Rank E (Recruta)',
    level INT NOT NULL DEFAULT 1,
    xp INT NOT NULL DEFAULT 0,
    next_level_xp INT NOT NULL DEFAULT 100,
    tasks_completed_lifetime INT NOT NULL DEFAULT 0,
    tasks_completed_today INT NOT NULL DEFAULT 0,
    last_audit_date DATE,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO rpg_player_state (id, player_name, title, rank, level, xp, next_level_xp)
VALUES (1, 'Matheus Silva', 'Sentinela Atalaia / Engenheiro', 'Rank E (Recruta)', 1, 0, 100)
ON CONFLICT (id) DO NOTHING;

CREATE TABLE IF NOT EXISTS rpg_quests (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title TEXT NOT NULL,
    quest_type TEXT NOT NULL DEFAULT 'Missão Diária',
    rank_difficulty TEXT DEFAULT 'Rank E',
    xp_reward INT DEFAULT 10,
    status TEXT DEFAULT 'pending',
    note_path TEXT,
    due_date DATE,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rpg_battle_log (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_type TEXT NOT NULL DEFAULT 'task_completed',
    description TEXT NOT NULL,
    xp_earned INT DEFAULT 10,
    evidence_path TEXT,
    logged_at TIMESTAMPTZ DEFAULT NOW()
);
