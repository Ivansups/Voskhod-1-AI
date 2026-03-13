"""Основная логика телеграм бота с управлением таймерами."""

import asyncio
import logging
from typing import Any, Dict

from aiogram import Bot

from .client import APIClient
from .config import TelegramConfig

logger = logging.getLogger(__name__)


class ChatBot:
    """Основной сервис телеграм бота с управлением диалогами."""

    def __init__(self, api_client: APIClient, bot: Bot, config: TelegramConfig):
        self.api_client = api_client
        self.bot = bot
        self.config = config

        self.active_timers: Dict[int, asyncio.Task] = {}
        self.chat_histories: Dict[int, list] = {}

    async def start_inactivity_timer(self, user_id: int) -> None:
        """
        Запустить таймер бездействия для пользователя.

        Args:
            user_id: ID пользователя Telegram
        """
        await self._cancel_timer(user_id)

        self.active_timers[user_id] = asyncio.create_task(
            self._inactivity_timer(user_id)
        )

        logger.info(f"Started inactivity timer for user {user_id}")

    async def reset_timer(self, user_id: int) -> None:
        """
        Сбросить таймер при активности пользователя.

        Args:
            user_id: ID пользователя Telegram
        """
        await self.start_inactivity_timer(user_id)

    async def _cancel_timer(self, user_id: int) -> None:
        """
        Отменить таймер для пользователя.

        Args:
            user_id: ID пользователя Telegram
        """
        if user_id in self.active_timers:
            self.active_timers[user_id].cancel()
            try:
                await self.active_timers[user_id]
            except asyncio.CancelledError:
                pass
            del self.active_timers[user_id]
            logger.info(f"Cancelled timer for user {user_id}")

    async def _inactivity_timer(self, user_id: int) -> None:
        """
        Таймер бездействия: 3 минуты с предупреждением.

        Args:
            user_id: ID пользователя Telegram
        """
        try:
            await asyncio.sleep(
                self.config.inactivity_timeout - self.config.warning_time
            )

            if user_id not in self.active_timers:
                return

            await self.bot.send_message(
                user_id,
                f"⚠️ Диалог завершится через {self.config.warning_time} секунд из-за бездействия",
            )

            await asyncio.sleep(self.config.warning_time)

            if user_id not in self.active_timers:
                return

            await self._end_chat(user_id, "из-за бездействия")

        except asyncio.CancelledError:
            logger.info(f"Timer cancelled for user {user_id}")
            raise

    async def _end_chat(self, user_id: int, reason: str) -> None:
        """
        Завершить диалог пользователя.

        Args:
            user_id: ID пользователя Telegram
            reason: Причина завершения
        """
        await self._cancel_timer(user_id)

        await self.bot.send_message(
            user_id,
            f"🔚 Диалог завершен {reason}.\n\n"
            "Напишите /start для начала нового диалога или /help для справки.",
        )

        if user_id in self.chat_histories:
            del self.chat_histories[user_id]

        from application.services.llm.llm_manager import get_llm_service

        llm_service = get_llm_service()
        llm_service.clear_history()

        logger.info(f"Chat ended for user {user_id}, reason: {reason}")

    async def start_chat(self, user_id: int) -> None:
        """
        Начать новый диалог с пользователем.

        Args:
            user_id: ID пользователя Telegram
        """
        self.chat_histories[user_id] = []

        from application.services.llm.llm_manager import get_llm_service

        llm_service = get_llm_service()
        llm_service.clear_history()

        await self.start_inactivity_timer(user_id)

        logger.info(f"Started new chat for user {user_id}")

    async def end_chat(
        self, user_id: int, reason: str = "по команде пользователя"
    ) -> None:
        """
        Завершить диалог по команде пользователя.

        Args:
            user_id: ID пользователя Telegram
            reason: Причина завершения
        """
        await self._end_chat(user_id, reason)

    async def add_to_history(self, user_id: int, message: str, response: str) -> None:
        """
        Добавить сообщение в историю чата.

        Args:
            user_id: ID пользователя Telegram
            message: Сообщение пользователя
            response: Ответ бота
        """
        if user_id not in self.chat_histories:
            self.chat_histories[user_id] = []

        self.chat_histories[user_id].append(
            {
                "user_message": message,
                "bot_response": response,
                "timestamp": asyncio.get_event_loop().time(),
            }
        )

        if len(self.chat_histories[user_id]) > 50:
            self.chat_histories[user_id] = self.chat_histories[user_id][-50:]

    async def get_history(self, user_id: int, limit: int = 10) -> list:
        """
        Получить историю чата пользователя.

        Args:
            user_id: ID пользователя Telegram
            limit: Максимальное количество сообщений

        Returns:
            Список сообщений из истории
        """
        if user_id not in self.chat_histories:
            return []

        history = self.chat_histories[user_id][-limit:]
        return history

    async def cleanup(self) -> None:
        """Очистка ресурсов при завершении работы."""
        for user_id, timer in self.active_timers.items():
            timer.cancel()

        if self.active_timers:
            await asyncio.gather(*self.active_timers.values(), return_exceptions=True)

        self.active_timers.clear()
        self.chat_histories.clear()

        await self.api_client.close()

        logger.info("Bot service cleanup completed")

    async def verify_api_key(
        self, api_key: str, user_tag: str = None
    ) -> Dict[str, Any]:
        """
        Проверяет API ключ через API с учетом user_tag.

        Args:
            api_key: API ключ для проверки
            user_tag: Тег пользователя для активации/проверки

        Returns:
            Dict с результатом проверки
        """
        try:
            params = {"key_value": api_key}
            if user_tag:
                params["user_tag"] = user_tag

            response = await self.api_client.client.post(
                f"{self.api_client.config.api_base_url}/v1/keys/verify", params=params
            )

            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Error verifying API key: {e}")
            return {"valid": False, "error": "API request failed"}

    async def check_user_activation(self, user_tag: str) -> dict:
        """
        Проверяет, есть ли у пользователя активированный ключ.

        Args:
            user_tag: Тег пользователя

        Returns:
            dict: Информация об активации ключа пользователя
        """
        try:
            response = await self.api_client.client.post(
                f"{self.api_client.config.api_base_url}/v1/keys/check_activation",
                params={"user_tag": user_tag},
            )

            if response.status_code == 200:
                result = response.json()
                return result
            else:
                logger.warning(
                    f"Failed to check user activation: {response.status_code}"
                )
                return {"has_activated_key": False}

        except Exception as e:
            logger.error(f"Error checking user activation: {e}")
            return False
