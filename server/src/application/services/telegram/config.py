"""Конфигурация телеграм бота."""

import os
from dataclasses import dataclass


@dataclass
class TelegramConfig:
    """Конфигурация для телеграм бота."""

    token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    api_base_url: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    inactivity_timeout: int = 180  # 3 минуты в секундах
    warning_time: int = 30  # Предупреждение за 30 секунд

    def validate(self) -> None:
        """Валидация конфигурации."""
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN не задан")
