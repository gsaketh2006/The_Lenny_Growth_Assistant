import os
import urllib.parse
from typing import Optional, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_db_url(url: str) -> str:
    """Normalizes database URL format for asyncpg and URL-encodes special password characters."""
    if not url:
        return "sqlite+aiosqlite:///./lenny_growth.db"
    
    # Normalize schema
    if url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]

    # Handle special characters in password (e.g. raw '@' before the final '@host')
    if "postgresql+asyncpg://" in url:
        prefix = "postgresql+asyncpg://"
        body = url[len(prefix):]
        if "@" in body:
            creds, host_part = body.rsplit("@", 1)
            if ":" in creds:
                user, password = creds.split(":", 1)
                encoded_password = urllib.parse.quote(urllib.parse.unquote(password))
                encoded_user = urllib.parse.quote(urllib.parse.unquote(user))
                url = f"{prefix}{encoded_user}:{encoded_password}@{host_part}"

    return url


class Settings(BaseSettings):
    """Application Settings with environment variable overrides."""

    PROJECT_NAME: str = "The Lenny Growth Assistant"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    ENVIRONMENT: str = "development"

    # Persistence / Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./lenny_growth.db"
    )

    # LLM Providers Configuration
    DEFAULT_LLM_PROVIDER: Literal["ollama", "anthropic", "openai"] = "ollama"
    
    # Local Ollama
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
    OLLAMA_EMBED_MODEL: str = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

    # Cloud Providers
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY", None)
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    OPENAI_EMBED_MODEL: str = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")

    # Local FastEmbed / SentenceTransformer fallback
    LOCAL_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384

    # RAG Retrieval Parameters
    TOP_K_RETRIEVAL: int = 5
    SIMILARITY_HIGH_THRESHOLD: float = 0.58
    SIMILARITY_MEDIUM_THRESHOLD: float = 0.42
    SIMILARITY_LOW_THRESHOLD: float = 0.28


    # Transcripts Archive Path
    TRANSCRIPTS_DIR: str = os.getenv(
        "TRANSCRIPTS_DIR",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/transcripts"))
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def effective_database_url(self) -> str:
        return normalize_db_url(self.DATABASE_URL)


settings = Settings()
