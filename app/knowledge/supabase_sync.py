"""Supabase pgvector synchronization engine for Obsidian Vault and SAO System v2.0."""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.core.config import logger, settings
from app.sao.manager import PlayerStats


@dataclass
class KnowledgeChunk:
    note_path: str
    note_title: str
    heading: str
    content: str
    tags: list[str]
    chunk_index: int
    word_count: int
    content_hash: str
    embedding: list[float] | None = None


class SupabaseVectorClient:
    """Zero-dependency HTTP client for Supabase PostgREST & pgvector API."""

    def __init__(
        self,
        supabase_url: str | None = None,
        api_key: str | None = None,
    ):
        self.base_url = (supabase_url or settings.supabase_url).rstrip("/")
        self.api_key = api_key or settings.supabase_service_role_key or settings.supabase_anon_key

    @property
    def is_configured(self) -> bool:
        return bool(
            self.base_url
            and self.api_key
            and len(self.api_key.strip()) > 20
            and "supabase.co" in self.base_url
        )

    def _request(
        self,
        endpoint: str,
        method: str = "GET",
        payload: Any = None,
        headers_extra: dict[str, str] | None = None,
    ) -> Any:
        if not self.is_configured:
            raise ValueError("Supabase não está configurado com URL e API Key.")

        url = f"{self.base_url}{endpoint}"
        headers = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if headers_extra:
            headers.update(headers_extra)

        data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else None
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8", errors="ignore")
            logger.error(f"Erro Supabase HTTP {e.code}: {err_msg}")
            raise RuntimeError(f"Supabase HTTP {e.code}: {err_msg}") from e
        except Exception as e:
            logger.error(f"Erro de conexão com Supabase: {e}")
            raise

    def upsert_chunks(self, chunks: list[KnowledgeChunk]) -> int:
        """Upsert knowledge chunks in batches using merge-duplicates."""
        if not chunks:
            return 0

        rows = []
        for c in chunks:
            rows.append({
                "note_path": c.note_path,
                "note_title": c.note_title,
                "heading": c.heading,
                "content": c.content,
                "tags": c.tags,
                "chunk_index": c.chunk_index,
                "word_count": c.word_count,
                "content_hash": c.content_hash,
                "embedding": c.embedding,
            })

        batch_size = 50
        total_upserted = 0
        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            self._request(
                "/rest/v1/knowledge_chunks?on_conflict=note_path,chunk_index",
                method="POST",
                payload=batch,
                headers_extra={"Prefer": "resolution=merge-duplicates,return=minimal"},
            )
            total_upserted += len(batch)

        return total_upserted

    def match_knowledge(
        self,
        query_embedding: list[float],
        threshold: float = 0.5,
        count: int = 5,
    ) -> list[dict[str, Any]]:
        """Call match_knowledge RPC function on Supabase."""
        payload = {
            "query_embedding": query_embedding,
            "match_threshold": threshold,
            "match_count": count,
        }
        res = self._request("/rest/v1/rpc/match_knowledge", method="POST", payload=payload)
        return res if isinstance(res, list) else []

    def sync_player_state(self, stats: PlayerStats) -> bool:
        """Mirror current player stats into rpg_player_state table."""
        payload = {
            "id": 1,
            "player_name": stats.name,
            "title": stats.title,
            "rank": stats.rank,
            "level": stats.level,
            "xp": stats.xp,
            "next_level_xp": stats.next_level_xp,
            "tasks_completed_lifetime": stats.tasks_completed_lifetime,
            "tasks_completed_today": stats.tasks_completed_today,
            "last_audit_date": stats.last_audit_date or None,
        }
        try:
            self._request(
                "/rest/v1/rpg_player_state?on_conflict=id",
                method="POST",
                payload=payload,
                headers_extra={"Prefer": "resolution=merge-duplicates,return=minimal"},
            )
            return True
        except Exception as e:
            logger.warning(f"Não foi possível sincronizar player state com Supabase: {e}")
            return False

    def log_sync(
        self,
        sync_type: str,
        notes_count: int,
        chunks_count: int,
        elapsed: float,
        status: str = "success",
        error: str | None = None,
    ) -> None:
        """Record sync telemetries."""
        payload = {
            "sync_type": sync_type,
            "notes_updated": notes_count,
            "chunks_total": chunks_count,
            "elapsed_seconds": round(elapsed, 3),
            "status": status,
            "error_message": error,
        }
        try:
            self._request(
                "/rest/v1/vault_sync_log",
                method="POST",
                payload=payload,
                headers_extra={"Prefer": "return=minimal"},
            )
        except Exception as e:
            logger.debug(f"Log sync não registrado no Supabase: {e}")


class EmbeddingGenerator:
    """Generates normalized vector embeddings using Gemini, OpenAI or deterministic fallback."""

    def __init__(self, dimension: int = 768):
        self.dimension = dimension

    def generate(self, text: str) -> list[float]:
        """Generate embedding for text. Falls back gracefully if API is unavailable."""
        clean_text = text.strip()[:8000]
        if not clean_text:
            return [0.0] * self.dimension

        # 1. Tentar Gemini se configurado
        if settings.gemini_api_key:
            vec = self._embed_gemini(clean_text)
            if vec:
                return vec

        # 2. Tentar OpenAI se configurado
        if settings.openai_api_key:
            vec = self._embed_openai(clean_text)
            if vec:
                return vec

        # 3. Fallback determinístico (reprodutível e seguro para testes sem rede/chaves)
        return self._embed_deterministic(clean_text)

    def _embed_gemini(self, text: str) -> list[float] | None:
        """Call Gemini text-embedding-004 endpoint."""
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"text-embedding-004:embedContent?key={settings.gemini_api_key}"
        )
        payload = {
            "model": "models/text-embedding-004",
            "content": {"parts": [{"text": text}]},
        }
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url, data=data, headers={"Content-Type": "application/json"}, method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                values = res.get("embedding", {}).get("values", [])
                if len(values) == self.dimension:
                    return values
        except Exception as e:
            logger.debug(f"Gemini embedding fallback: {e}")
        return None

    def _embed_openai(self, text: str) -> list[float] | None:
        """Call OpenAI text-embedding-3-small."""
        url = "https://api.openai.com/v1/embeddings"
        payload = {
            "input": text,
            "model": "text-embedding-3-small",
            "dimensions": self.dimension,
        }
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {settings.openai_api_key}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                return res["data"][0]["embedding"]
        except Exception as e:
            logger.debug(f"OpenAI embedding fallback: {e}")
        return None

    def _embed_deterministic(self, text: str) -> list[float]:
        """Fast, normalized deterministic pseudo-embedding for testing/offline use."""
        vec = []
        # Usa hashes múltiplos para povoar o espaço vetorial
        for i in range(self.dimension):
            h = hashlib.sha256(f"{i}_{text}".encode("utf-8")).digest()
            val = ((h[0] << 8) | h[1]) / 65535.0  # 0.0 to 1.0
            vec.append(val - 0.5)

        # Normalização L2
        norm = sum(x * x for x in vec) ** 0.5
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec


class VaultKnowledgeSynchronizer:
    """Orchestrates parsing of Obsidian Vault markdown notes and syncing to Supabase pgvector."""

    EXCLUDED_DIRS = {
        ".obsidian",
        ".claude",
        ".claudian",
        ".vscode",
        ".git",
        "jarvis",
        "node_modules",
        "venv",
        ".venv",
        "__pycache__",
        ".pytest_cache",
    }

    def __init__(
        self,
        vault_path: Path | None = None,
        supabase_client: SupabaseVectorClient | None = None,
    ):
        self.vault_path = vault_path or settings.vault_path
        self.client = supabase_client or SupabaseVectorClient()
        self.embedder = EmbeddingGenerator(dimension=settings.embedding_dimension)

    def scan_and_chunk_vault(self) -> list[KnowledgeChunk]:
        """Scan all markdown files in the vault and produce structured knowledge chunks."""
        chunks: list[KnowledgeChunk] = []

        if not self.vault_path.exists():
            logger.warning(f"Cofre não encontrado em {self.vault_path}")
            return chunks

        for root, dirs, files in os.walk(self.vault_path):
            # Filtro de pastas ignoradas
            dirs[:] = [d for d in dirs if d not in self.EXCLUDED_DIRS]

            for file in files:
                if not file.endswith(".md"):
                    continue

                full_path = Path(root) / file
                rel_path = full_path.relative_to(self.vault_path).as_posix()

                try:
                    note_chunks = self._chunk_note(full_path, rel_path)
                    chunks.extend(note_chunks)
                except Exception as e:
                    logger.error(f"Erro ao processar nota {rel_path}: {e}")

        return chunks

    def _chunk_note(self, file_path: Path, rel_path: str) -> list[KnowledgeChunk]:
        """Break down a single note into semantic sections based on headers."""
        raw_text = file_path.read_text(encoding="utf-8", errors="replace")
        note_title = file_path.stem

        # Extrair frontmatter e tags
        tags = re.findall(r"#([\w\-_/]+)", raw_text)
        # Quebrar por cabeçalhos markdown
        header_pattern = re.compile(r"^(#{1,4}\s+.+)$", re.MULTILINE)
        parts = header_pattern.split(raw_text)

        chunks: list[KnowledgeChunk] = []
        current_heading = "Introdução"
        index = 0

        # Primeiro bloco antes do primeiro header (se houver)
        if parts:
            first_block = parts[0].strip()
            if first_block and len(first_block) > 20:
                h = hashlib.sha256(first_block.encode("utf-8")).hexdigest()
                chunks.append(
                    KnowledgeChunk(
                        note_path=rel_path,
                        note_title=note_title,
                        heading=current_heading,
                        content=first_block,
                        tags=list(set(tags)),
                        chunk_index=index,
                        word_count=len(first_block.split()),
                        content_hash=h,
                    )
                )
                index += 1

        # Iterar sobre pares (header, conteúdo)
        for i in range(1, len(parts), 2):
            heading_line = parts[i].strip()
            content_block = parts[i + 1].strip() if i + 1 < len(parts) else ""

            heading_clean = heading_line.lstrip("#").strip()
            full_section = f"{heading_line}\n\n{content_block}".strip()

            if len(full_section) < 15:
                continue

            h = hashlib.sha256(full_section.encode("utf-8")).hexdigest()
            chunks.append(
                KnowledgeChunk(
                    note_path=rel_path,
                    note_title=note_title,
                    heading=heading_clean,
                    content=full_section,
                    tags=list(set(tags)),
                    chunk_index=index,
                    word_count=len(full_section.split()),
                    content_hash=h,
                )
            )
            index += 1

        return chunks

    def sync_to_supabase(self) -> dict[str, Any]:
        """Run full sync workflow: scan vault, generate embeddings, upsert to Supabase."""
        start_time = time.time()
        logger.info("Iniciando sincronização do cofre com Supabase...")

        chunks = self.scan_and_chunk_vault()
        total_chunks = len(chunks)
        notes_paths = {c.note_path for c in chunks}

        if not self.client.is_configured:
            return {
                "success": False,
                "configured": False,
                "message": (
                    "Supabase não configurado. Adicione SUPABASE_URL e SUPABASE_ANON_KEY no jarvis/.env. "
                    f"Foram identificados {len(notes_paths)} notas e {total_chunks} chunks prontos para sincronia."
                ),
                "notes_count": len(notes_paths),
                "chunks_count": total_chunks,
            }

        # Gerar embeddings para cada chunk
        for chunk in chunks:
            chunk.embedding = self.embedder.generate(f"{chunk.note_title} - {chunk.heading}\n{chunk.content}")

        # Enviar para Supabase
        try:
            upserted = self.client.upsert_chunks(chunks)
            elapsed = time.time() - start_time

            self.client.log_sync(
                sync_type="full",
                notes_count=len(notes_paths),
                chunks_count=upserted,
                elapsed=elapsed,
                status="success",
            )

            return {
                "success": True,
                "configured": True,
                "notes_count": len(notes_paths),
                "chunks_upserted": upserted,
                "elapsed_seconds": round(elapsed, 2),
            }
        except Exception as e:
            elapsed = time.time() - start_time
            self.client.log_sync(
                sync_type="full",
                notes_count=len(notes_paths),
                chunks_count=0,
                elapsed=elapsed,
                status="error",
                error=str(e),
            )
            return {
                "success": False,
                "configured": True,
                "error": str(e),
                "notes_count": len(notes_paths),
                "chunks_count": total_chunks,
            }

    def semantic_search(self, query: str, count: int = 5, threshold: float = 0.4) -> list[dict[str, Any]]:
        """Search Supabase vector store for matching knowledge sections with automatic local fallback."""
        if not query.strip():
            return []

        def _local_search() -> list[dict[str, Any]]:
            chunks = self.scan_and_chunk_vault()
            q_lower = query.lower()
            matches = []
            for c in chunks:
                if q_lower in c.content.lower() or q_lower in c.note_title.lower():
                    matches.append({
                        "note_path": c.note_path,
                        "note_title": c.note_title,
                        "heading": c.heading,
                        "content": c.content[:300] + "...",
                        "similarity": 0.85 if q_lower in c.note_title.lower() else 0.65,
                    })
            matches.sort(key=lambda x: x["similarity"], reverse=True)
            return matches[:count]

        if not self.client.is_configured:
            return _local_search()

        # Supabase vetorial
        query_vec = self.embedder.generate(query)
        try:
            res = self.client.match_knowledge(query_vec, threshold=threshold, count=count)
            if res:
                return res
        except Exception as e:
            logger.warning(f"Erro na busca vetorial Supabase ({e}). Recorrendo à busca local.")

        return _local_search()


if __name__ == "__main__":
    sync = VaultKnowledgeSynchronizer()
    res = sync.sync_to_supabase()
    print("Resultado da Sincronização:", json.dumps(res, indent=2, ensure_ascii=False))
