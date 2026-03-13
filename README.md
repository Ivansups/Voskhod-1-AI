# Voskhod-1 AI

Интеллектуальная система для работы с учебными материалами на базе RAG (Retrieval-Augmented Generation).

## 🚀 Быстрый старт

### Полный запуск с автоматической индексацией
```bash
./start-with-indexing.sh
```

Эта команда:
- 🚀 Запустит все сервисы (PostgreSQL, Qdrant, Redis, API)
- 📊 Выполнит индексацию документов
- ⏰ Покажет прогресс в реальном времени
- 🎯 Сделает систему готовой к работе

### Ручное управление

#### Запуск сервисов
```bash
docker-compose up -d
```

#### Индексация документов
```bash
# Умная индексация (проверяет актуальность)
./scripts/docker-indexing.sh

# Принудительная полная переиндексация
./scripts/docker-indexing.sh force

# Автоматический мониторинг (работает в фоне)
./scripts/docker-indexing.sh monitor
```

#### Проверка статуса
```bash
./scripts/check_indexing_status.sh
```

## 🏗️ Архитектура

- **FastAPI** - REST API сервер
- **Qdrant** - векторная база данных
- **PostgreSQL** - реляционная БД
- **Redis** - кэширование
- **Ollama/OpenRouter** - LLM провайдеры

## 📚 Документация

- [Индексация документов](docs/INDEXING_README.md) - подробная информация об индексации
- [Telegram бот](server/README_TELEGRAM_BOT.md) - интеграция с Telegram
- `plans/` - архитектурные заметки и планы разработки

## 🔧 Переменные окружения

Создайте `.env` файл на основе `.env.example`:

```bash
cp .env.example .env
```

Основные переменные:
- `OPENROUTER_API_KEY` - API ключ для OpenRouter
- `TELEGRAM_BOT_TOKEN` - токен Telegram бота
- `GIT_REPO_URL` - URL git репозитория с документами

## 📊 Мониторинг

- **API**: http://localhost:8000
- **Qdrant**: http://localhost:6333
- **Статус индексации**: http://localhost:8000/v1/admin/sync/status

## 🛠️ Разработка

```bash
# Установка зависимостей
poetry install

# Линтер и форматирование
ruff check .
ruff format .

# Запуск в режиме разработки
docker-compose -f docker-compose.yml -f docker-compose.override.yml up
```

## 📝 Лицензия

MIT