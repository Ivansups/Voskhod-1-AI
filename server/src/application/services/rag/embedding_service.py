import abc
import asyncio
import logging
from typing import List, Optional

import httpx
from application.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService(abc.ABC):
    """Абстрактный класс для сервисов генерации эмбеддингов."""

    @abc.abstractmethod
    async def embed(self, text: str) -> List[float]:
        """
        Генерирует эмбеддинг для текста.

        Args:
            text: Текст для векторизации

        Returns:
            Список чисел (вектор эмбеддинга)
        """
        pass

    @abc.abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Генерирует эмбеддинги для списка текстов.

        Args:
            texts: Список текстов для векторизации

        Returns:
            Список векторов эмбеддингов
        """
        pass

    @abc.abstractmethod
    def get_vector_size(self) -> int:
        """
        Возвращает размерность вектора эмбеддинга.

        Returns:
            Размерность вектора
        """
        pass


class OpenAIEmbeddingService(EmbeddingService):
    """Сервис генерации эмбеддингов через OpenAI API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY не установлен")

        self.model = model or settings.OPENAI_EMBEDDING_MODEL
        self.base_url = "https://api.openai.com/v1"
        self.client = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def close(self):
        """Закрывает HTTP клиент."""
        await self.client.aclose()

    async def embed(self, text: str) -> List[float]:
        """Генерирует эмбеддинг для текста через OpenAI API."""
        url = f"{self.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": self.model, "input": text}

        try:
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            return result["data"][0]["embedding"]
        except httpx.HTTPStatusError as e:
            raise ConnectionError(f"Ошибка генерации эмбеддинга через OpenAI: {e}")

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Генерирует эмбеддинги для списка текстов через OpenAI API."""
        url = f"{self.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": self.model, "input": texts}

        try:
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            return [item["embedding"] for item in result["data"]]
        except httpx.HTTPStatusError as e:
            raise ConnectionError(f"Ошибка генерации эмбеддингов через OpenAI: {e}")

    def get_vector_size(self) -> int:
        """Возвращает размерность вектора для OpenAI модели."""
        if "3-small" in self.model:
            return 1536
        elif "3-large" in self.model:
            return 3072
        elif "ada-002" in self.model:
            return 1536
        else:
            return 1536


class OllamaEmbeddingService(EmbeddingService):
    """Сервис генерации эмбеддингов через Ollama API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_EMBEDDING_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_EMBEDDING_MODEL
        self.client = httpx.AsyncClient(timeout=120.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def close(self):
        """Закрывает HTTP клиент."""
        await self.client.aclose()

    def _is_retryable_error(self, exc: BaseException) -> bool:
        """Проверяет, является ли ошибка временной (retryable)."""
        if isinstance(exc, httpx.TimeoutException):
            return True
        if isinstance(exc, httpx.ConnectError):
            return True
        if isinstance(exc, httpx.HTTPStatusError):
            status = getattr(exc, "response", None) and getattr(
                exc.response, "status_code", None
            )
            if status:
                return status >= 500 or status == 429
        return False

    async def embed(self, text: str) -> List[float]:
        """Генерирует эмбеддинг для текста через Ollama API с retry и exponential backoff."""
        url = f"{self.base_url}/api/embeddings"
        payload = {"model": self.model, "prompt": text}
        max_retries = settings.EMBEDDING_MAX_RETRIES
        base_delay_ms = settings.EMBEDDING_RETRY_BASE_DELAY_MS
        max_delay_sec = 30

        last_exc = None
        for attempt in range(max_retries + 1):
            try:
                response = await self.client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                embedding = result.get("embedding", [])
                if not embedding:
                    raise ValueError("Пустой эмбеддинг от Ollama API")
                return embedding
            except (
                httpx.TimeoutException,
                httpx.ConnectError,
                httpx.HTTPStatusError,
            ) as e:
                last_exc = e
                if not self._is_retryable_error(e) or attempt >= max_retries:
                    raise
                delay_sec = min(
                    (base_delay_ms / 1000.0) * (2**attempt),
                    max_delay_sec,
                )
                logger.warning(
                    "Ollama embedding retry %d/%d after %s: %s",
                    attempt + 1,
                    max_retries,
                    type(e).__name__,
                    str(e),
                )
                await asyncio.sleep(delay_sec)
        if last_exc:
            raise last_exc
        raise RuntimeError("Unexpected embed() loop exit")

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Генерирует эмбеддинги для списка текстов через Ollama API с throttling."""
        embeddings = []
        batch_size = settings.EMBEDDING_BATCH_SIZE
        delay_sec = settings.EMBEDDING_DELAY_MS / 1000.0

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            for text in batch:
                embedding = await self.embed(text)
                embeddings.append(embedding)
                if delay_sec > 0:
                    await asyncio.sleep(delay_sec)
            # Пауза между мини-батчами (если есть следующий батч)
            if i + batch_size < len(texts) and delay_sec > 0:
                await asyncio.sleep(delay_sec)
        return embeddings

    def get_vector_size(self) -> int:
        """Возвращает размерность вектора для Ollama модели."""
        if "mxbai-embed-large" in self.model:
            return 1024
        elif "nomic-embed" in self.model:
            return 768
        else:
            return 768


def get_embedding_service() -> EmbeddingService:
    """
    Фабричная функция для создания сервиса эмбеддингов на основе переменных окружения.

    Returns:
        Экземпляр EmbeddingService (OpenAI или Ollama)
    """
    service_type = settings.EMBEDDING_SERVICE

    if service_type == "ollama":
        return OllamaEmbeddingService()
    else:
        return OpenAIEmbeddingService()
