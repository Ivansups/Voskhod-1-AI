#!/usr/bin/env python3
"""
Скрипт для индексации документов внутри контейнера.
Запускается автоматически при старте сервиса индексации.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from application.services.git_sync.sync_service import GitSyncService

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def run_indexing(force_reindex: bool = False):
    """Запуск индексации документов."""

    logger.info("🚀 Запуск индексации документов в контейнере")
    logger.info("=" * 60)

    try:
        # Инициализируем сервис синхронизации
        sync_service = GitSyncService()

        # Запускаем синхронизацию и индексацию
        result = await sync_service.sync_and_index(force_full_reindex=force_reindex)

        if result["success"]:
            index_status = result.get("index_status", {})

            if index_status.get("skipped"):
                logger.info("✅ Данные уже актуальные, индексация пропущена")
            else:
                logger.info("✅ Индексация завершена успешно")
                logger.info(
                    f"📊 Обработано файлов: {index_status.get('files_processed', 0)}"
                )
                logger.info(
                    f"📊 Создано чанков: {index_status.get('indexed_chunks', 0)}"
                )
        else:
            logger.error(
                f"❌ Ошибка индексации: {result.get('error', 'Неизвестная ошибка')}"
            )
            return False

        return True

    except Exception as e:
        logger.error(f"❌ Критическая ошибка при индексации: {e}")
        return False


async def monitor_and_reindex():
    """Мониторинг и периодическая переиндексация."""

    logger.info("🔄 Запуск сервиса автоматической индексации")
    logger.info("📅 Проверка каждые 60 минут")

    # Начальная индексация при старте
    logger.info("🏁 Выполняем начальную индексацию...")
    await run_indexing(force_reindex=False)

    # Периодическая проверка и индексация
    while True:
        try:
            logger.info("⏰ Ожидание следующей проверки (60 минут)...")
            await asyncio.sleep(60 * 60)  # 60 минут

            logger.info("🔍 Проверяем необходимость индексации...")
            await run_indexing(force_reindex=False)

        except KeyboardInterrupt:
            logger.info("🛑 Сервис индексации остановлен")
            break
        except Exception as e:
            logger.error(f"❌ Ошибка в цикле индексации: {e}")
            await asyncio.sleep(300)  # Ждем 5 минут перед следующей попыткой


async def main():
    """Основная функция."""

    # Определяем режим работы
    mode = os.getenv("INDEXER_MODE", "once")  # once, monitor, force

    if mode == "force":
        logger.info("💪 Режим: Принудительная полная индексация")
        success = await run_indexing(force_reindex=True)
    elif mode == "monitor":
        logger.info("🔄 Режим: Автоматический мониторинг")
        await monitor_and_reindex()
    else:  # once (по умолчанию)
        logger.info("📄 Режим: Одноразовая индексация")
        success = await run_indexing(force_reindex=False)

    # Выходим с соответствующим кодом
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
