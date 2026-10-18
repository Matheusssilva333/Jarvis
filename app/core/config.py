"""Configuration management and system environment validation."""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Base Paths
    root_dir: Path = Path(__file__).resolve().parent.parent.parent
    obsidian_vault_path: str = Field(default="..")

    # LLM & Providers
    default_llm_provider: Literal["gemini", "claude", "openai", "ollama"] = "gemini"
    gemini_api_key: str = ""
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Ollama Local Configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:1.5b-instruct"

    # Embeddings & RAG
    embedding_provider: str = "local_cpu"
    embedding_model: str = "all-MiniLM-L6-v2"
    max_search_results: int = 5
    similarity_threshold: float = 0.65

    # Security
    security_level: int = Field(default=2, ge=1, le=4)

    # Supabase Second Brain
    supabase_url: str = "https://etztvnzxkhdoqwswajgb.supabase.co"
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    embedding_dimension: int = 768

    # SAO Gamification
    sao_system_enabled: bool = True
    xp_per_task: int = 10

    @property
    def vault_path(self) -> Path:
        """Resolve and validate the absolute path to the Obsidian Vault."""
        path = Path(self.obsidian_vault_path)
        if not path.is_absolute():
            path = (self.root_dir / path).resolve()
        return path

    @property
    def data_dir(self) -> Path:
        """Directory for SQLite, cache, and runtime artifacts."""
        path = self.root_dir / "data"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def db_path(self) -> Path:
        """SQLite database file path."""
        return self.data_dir / "jarvis.db"

    @property
    def logs_dir(self) -> Path:
        """Directory for operational audit logs."""
        path = self.data_dir / "logs"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def backups_dir(self) -> Path:
        """Directory for safe rollback snapshots."""
        path = self.data_dir / "backups"
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure structured logging to console and persistent log file."""
    log_file = settings.logs_dir / "jarvis_audit.log"

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger = logging.getLogger("jarvis")
    logger.setLevel(level)

    # Avoid duplicate handlers on re-init
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


logger = setup_logging()
