#!/usr/bin/env python3
"""Запуск телеграм бота."""

import sys
from pathlib import Path

# Добавляем путь к исходному коду
sys.path.insert(0, str(Path(__file__).parent / "server" / "src"))

# Импортируем и запускаем основную функцию бота
from application.services.telegram.main import main

if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
