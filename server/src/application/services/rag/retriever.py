from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

from application.infrastructure.vector_db.qdrant_client import QdrantClient
from .embedding_service import EmbeddingService
from application.core.config import settings


class RAGRetriever:
    """Класс для поиска релевантных чанков в векторной БД."""

    def __init__(
        self,
        qdrant_client: QdrantClient,
        embedding_service: EmbeddingService,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None,
    ):
        self.qdrant_client = qdrant_client
        self.embedding_service = embedding_service
        self.top_k = top_k or settings.RAG_TOP_K
        self.score_threshold = score_threshold or settings.RAG_SCORE_THRESHOLD

    async def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Ищет релевантные чанки для запроса.

        Args:
            query: Текст запроса
            top_k: Количество результатов (по умолчанию используется self.top_k)
            score_threshold: Минимальный порог схожести (по умолчанию используется self.score_threshold)
            filter: Фильтр по метаданным

        Returns:
            Список словарей с полями:
            - content: Текст чанка
            - score: Оценка релевантности
            - metadata: Метаданные (source, file_path, chunk_index)
        """
        # Генерируем эмбеддинг для запроса
        query_vector = await self.embedding_service.embed(query)

        # Ищем похожие векторы в Qdrant
        k = top_k or self.top_k
        threshold = (
            score_threshold if score_threshold is not None else self.score_threshold
        )

        results = await self.qdrant_client.search(
            vector=query_vector, top_k=k, score_threshold=threshold, filter=filter
        )

        # Форматируем результаты
        formatted_results = []
        for result in results:
            formatted_results.append(
                {
                    "content": result.get("content", ""),
                    "score": result.get("score", 0.0),
                    "metadata": result.get("metadata", {}),
                    "id": result.get("id"),
                }
            )

        return formatted_results

    async def retrieve_with_context(
        self,
        query: str,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None,
        filter: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Ищет релевантные чанки и возвращает их как объединенный контекст.

        Args:
            query: Текст запроса
            top_k: Количество результатов
            score_threshold: Минимальный порог схожести
            filter: Фильтр по метаданным

        Returns:
            Объединенный текст всех найденных чанков
        """
        results = await self.retrieve(query, top_k, score_threshold, filter)

        # Объединяем содержимое чанков
        context_parts = []
        for i, result in enumerate(results, 1):
            content = result.get("content", "")
            source = result.get("metadata", {}).get("source", "unknown")
            context_parts.append(f"[{i}] Источник: {source}\n{content}")

        return "\n\n".join(context_parts)
