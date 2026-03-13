"""Главная точка входа для телеграм бота."""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from aiogram import Bot, Dispatcher

from .bot_service import ChatBot
from .client import APIClient
from .config import TelegramConfig
from .handlers.commands import commands_router
from .handlers.messages import messages_router


async def main() -> None:
    """Главная функция запуска бота."""
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("telegram_bot.log", encoding="utf-8"),
        ],
    )

    logger = logging.getLogger(__name__)

    try:
        config = TelegramConfig()
        config.validate()

        logger.info("Configuration loaded successfully")

        api_client = APIClient(config)
        bot = Bot(token=config.token)
        dp = Dispatcher()

        bot_service = ChatBot(api_client, bot, config)

        dp["bot_service"] = bot_service

        dp.include_router(commands_router)
        dp.include_router(messages_router)

        logger.info("Bot components initialized successfully")

        logger.info("Starting telegram bot...")
        await dp.start_polling(bot, close_bot_session=True)

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")

    except Exception as e:
        logger.error(f"Critical error: {e}")
        raise

    finally:
        if "bot_service" in locals():
            await bot_service.cleanup()
        if "api_client" in locals():
            await api_client.close()

        logger.info("Bot shutdown complete")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
