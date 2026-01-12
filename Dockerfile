# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    git \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Poetry
RUN pip install poetry

# Создаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY pyproject.toml poetry.lock* ./

# Настраиваем Poetry (не создавать виртуальное окружение)
RUN poetry config virtualenvs.create false

# Устанавливаем зависимости
RUN poetry install --without dev --no-root --no-interaction

# Копируем исходный код
COPY server/ ./server/

# Создаем непривилегированного пользователя
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Настраиваем PYTHONPATH для правильного поиска модулей
ENV PYTHONPATH=/app/server/src:$PYTHONPATH

# Экспортируем порт
EXPOSE 8000

# Запускаем приложение
WORKDIR /app/server/src
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
