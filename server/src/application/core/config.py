import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Централизованная конфигурация приложения из переменных окружения."""

    # PostgreSQL
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "voskhod_ai")

    @property
    def POSTGRES_URL(self) -> str:
        """URL для подключения к PostgreSQL."""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Qdrant
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY: Optional[str] = os.getenv("QDRANT_API_KEY")
    QDRANT_COLLECTION_NAME: str = os.getenv(
        "QDRANT_COLLECTION_NAME", "university_knowledge"
    )

    # RAG
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))
    RAG_SCORE_THRESHOLD: float = float(os.getenv("RAG_SCORE_THRESHOLD", "0.7"))

    # Embeddings - OpenAI
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_EMBEDDING_MODEL: str = os.getenv(
        "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
    )

    # Embeddings - Ollama
    OLLAMA_EMBEDDING_BASE_URL: str = os.getenv(
        "OLLAMA_EMBEDDING_BASE_URL", "http://localhost:11434"
    )
    OLLAMA_EMBEDDING_MODEL: str = os.getenv(
        "OLLAMA_EMBEDDING_MODEL", "nomic-embed-text"
    )

    # Embeddings - выбор сервиса
    EMBEDDING_SERVICE: str = os.getenv("EMBEDDING_SERVICE", "ollama").lower()

    # Embeddings - throttling и retries (provider-specific defaults)
    @property
    def EMBEDDING_DELAY_MS(self) -> int:
        val = os.getenv("EMBEDDING_DELAY_MS")
        if val is not None:
            return int(val)
        return 300 if self.EMBEDDING_SERVICE == "ollama" else 0

    @property
    def EMBEDDING_BATCH_SIZE(self) -> int:
        val = os.getenv("EMBEDDING_BATCH_SIZE")
        if val is not None:
            return int(val)
        return 10 if self.EMBEDDING_SERVICE == "ollama" else 100

    @property
    def EMBEDDING_MAX_RETRIES(self) -> int:
        val = os.getenv("EMBEDDING_MAX_RETRIES")
        if val is not None:
            return int(val)
        return 3 if self.EMBEDDING_SERVICE == "ollama" else 2

    @property
    def EMBEDDING_RETRY_BASE_DELAY_MS(self) -> int:
        val = os.getenv("EMBEDDING_RETRY_BASE_DELAY_MS")
        if val is not None:
            return int(val)
        return 1000 if self.EMBEDDING_SERVICE == "ollama" else 500

    @property
    def INDEXER_FILE_DELAY_MS(self) -> int:
        val = os.getenv("INDEXER_FILE_DELAY_MS")
        if val is not None:
            return int(val)
        return 1500 if self.EMBEDDING_SERVICE == "ollama" else 0

    # LLM - OpenRouter
    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_MODEL: Optional[str] = os.getenv("OPENROUTER_MODEL")
    OPENROUTER_TEMPERATURE: Optional[float] = (
        float(os.getenv("OPENROUTER_TEMPERATURE"))
        if os.getenv("OPENROUTER_TEMPERATURE")
        else None
    )
    OPENROUTER_MAX_TOKENS: Optional[int] = (
        int(os.getenv("OPENROUTER_MAX_TOKENS"))
        if os.getenv("OPENROUTER_MAX_TOKENS")
        else None
    )

    # LLM - Ollama
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
    OLLAMA_TEMPERATURE: Optional[float] = (
        float(os.getenv("OLLAMA_TEMPERATURE"))
        if os.getenv("OLLAMA_TEMPERATURE")
        else 0.7
    )
    OLLAMA_MAX_TOKENS: Optional[int] = (
        int(os.getenv("OLLAMA_MAX_TOKENS")) if os.getenv("OLLAMA_MAX_TOKENS") else 1000
    )

    # API
    # API_KEY: Optional[str] = os.getenv("API_KEY")  # Removed: legacy static key

    # Git Sync
    GIT_REPO_URL: str = os.getenv("GIT_REPO_URL", "")
    GIT_LOCAL_PATH: str = os.getenv("GIT_LOCAL_PATH", "./data/git_repo")
    GIT_BRANCH: str = os.getenv("GIT_BRANCH", "main")
    GIT_SYNC_INTERVAL_MINUTES: int = int(os.getenv("GIT_SYNC_INTERVAL_MINUTES", "60"))


# Глобальный экземпляр настроек
settings = Settings()
