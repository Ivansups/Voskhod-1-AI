from typing import Any, Dict, List, Optional

import httpx
from application.core.config import settings


class QdrantClient:
    """Асинхронный клиент для работы с Qdrant векторной БД."""

    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        collection_name: Optional[str] = None,
    ):
        self.url = (url or settings.QDRANT_URL).rstrip("/")
        self.api_key = api_key or settings.QDRANT_API_KEY
        self.collection_name = collection_name or settings.QDRANT_COLLECTION_NAME

        self.headers = {}
        if self.api_key:
            self.headers["api-key"] = self.api_key

        self.client = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def close(self):
        """Закрывает HTTP клиент."""
        await self.client.aclose()

    async def create_collection(
        self,
        collection_name: Optional[str] = None,
        vector_size: int = 1536,
        distance: str = "Cosine",
    ) -> Dict[str, Any]:
        """
        Создает коллекцию в Qdrant.

        Args:
            collection_name: Имя коллекции (по умолчанию используется self.collection_name)
            vector_size: Размерность векторов
            distance: Метрика расстояния (Cosine, Euclidean, Dot)

        Returns:
            Результат создания коллекции
        """
        name = collection_name or self.collection_name
        url = f"{self.url}/collections/{name}"

        payload = {"vectors": {"size": vector_size, "distance": distance}}

        try:
            response = await self.client.put(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                # Коллекция уже существует
                return {"status": "exists", "collection": name}
            raise ConnectionError(f"Ошибка создания коллекции в Qdrant: {e}")

    async def search(
        self,
        vector: List[float],
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        collection_name: Optional[str] = None,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Поиск похожих векторов в коллекции.

        Args:
            vector: Вектор для поиска
            top_k: Количество результатов
            score_threshold: Минимальный порог схожести
            collection_name: Имя коллекции (по умолчанию используется self.collection_name)
            filter: Фильтр по метаданным

        Returns:
            Список результатов с полями: id, score, payload
        """
        name = collection_name or self.collection_name
        url = f"{self.url}/collections/{name}/points/search"

        payload = {
            "vector": vector,
            "limit": top_k,
            "with_payload": True,
            "with_vector": False,
        }

        if score_threshold is not None:
            payload["score_threshold"] = score_threshold

        if filter:
            payload["filter"] = filter

        try:
            response = await self.client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            result = response.json()

            results = []
            for item in result.get("result", []):
                results.append(
                    {
                        "id": item.get("id"),
                        "score": item.get("score", 0.0),
                        "payload": item.get("payload", {}),
                        "content": item.get("payload", {}).get("content", ""),
                        "metadata": {
                            "source": item.get("payload", {}).get("source", ""),
                            "file_path": item.get("payload", {}).get("file_path", ""),
                            "chunk_index": item.get("payload", {}).get(
                                "chunk_index", 0
                            ),
                        },
                    }
                )

            return results
        except httpx.HTTPStatusError as e:
            raise ConnectionError(f"Ошибка поиска в Qdrant: {e}")

    async def upsert(
        self, points: List[Dict[str, Any]], collection_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Добавляет или обновляет точки в коллекции.

        Args:
            points: Список точек в формате [{"id": ..., "vector": ..., "payload": {...}}, ...]
            collection_name: Имя коллекции (по умолчанию используется self.collection_name)

        Returns:
            Результат операции
        """
        name = collection_name or self.collection_name
        url = f"{self.url}/collections/{name}/points"

        payload = {"points": points}

        try:
            response = await self.client.put(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise ConnectionError(f"Ошибка добавления точек в Qdrant: {e}")

    async def delete(
        self, point_ids: List[str], collection_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Удаляет точки из коллекции.

        Args:
            point_ids: Список ID точек для удаления
            collection_name: Имя коллекции (по умолчанию используется self.collection_name)

        Returns:
            Результат операции
        """
        name = collection_name or self.collection_name
        url = f"{self.url}/collections/{name}/points/delete"

        payload = {"points": point_ids}

        try:
            response = await self.client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise ConnectionError(f"Ошибка удаления точек из Qdrant: {e}")

    async def list_collections(self) -> Dict[str, Any]:
        """
        Получает список всех коллекций.

        Returns:
            Dict с результатом и списком коллекций
        """
        url = f"{self.url}/collections"

        try:
            response = await self.client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise ConnectionError(f"Ошибка получения списка коллекций: {e}")

    async def get_collection_info(
        self, collection_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Получает информацию о коллекции.

        Args:
            collection_name: Имя коллекции (по умолчанию используется self.collection_name)

        Returns:
            Информация о коллекции
        """
        name = collection_name or self.collection_name
        url = f"{self.url}/collections/{name}"

        try:
            response = await self.client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return {"exists": False}
            raise ConnectionError(f"Ошибка получения информации о коллекции: {e}")
