"""HTTP клиент для интеграции с FastAPI."""

from typing import Any, Dict, Optional

import httpx

from .config import TelegramConfig


class APIClient:
    """HTTP клиент для общения с RAG API."""

    def __init__(self, config: TelegramConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            headers={"Content-Type": "application/json"}, timeout=30.0
        )

    async def chat(self, question: str) -> Dict[str, Any]:
        """
        Отправить вопрос в RAG API.

        Args:
            question: Вопрос пользователя

        Returns:
            Dict с ответом API

        Raises:
            httpx.HTTPError: При ошибках HTTP
        """
        url = f"{self.config.api_base_url}/v1/chat"

        response = await self.client.post(url, json={"question": question})

        response.raise_for_status()
        return response.json()

    async def get_chat_history(self, limit: int = 10) -> Optional[Dict[str, Any]]:
        """
        Получить историю чата (если эндпоинт реализован).

        Args:
            limit: Количество сообщений для получения

        Returns:
            История чата или None если не реализовано
        """
        try:
            url = f"{self.config.api_base_url}/v1/chat/history"
            response = await self.client.get(url, params={"limit": limit})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            # Если эндпоинт не реализован, возвращаем None
            return None

    async def close(self) -> None:
        """Закрыть HTTP клиент."""
        await self.client.aclose()
