# Voskhod AI - Docker Setup

Полный стек AI-ассистента университета с RAG-системой и Telegram ботом в Docker контейнерах.

## 🚀 **Обновлено: OpenRouter + Ollama**

- **LLM**: OpenRouter (GPT модели через единый API)
- **Embeddings**: Ollama (локальная векторизация, без API ключей)
- **Базы данных**: PostgreSQL, Qdrant, Redis

## 🏗 Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram Bot  │    │    FastAPI      │    │   PostgreSQL    │
│                 │    │   Application   │    │     Database    │
│   aiogram 3.x   │◄──►│                 │◄──►│                 │
│                 │    │  RAG Engine     │    │   API Keys      │
└─────────────────┘    │                 │    │   Chat Logs     │
                       └─────────────────┘    └─────────────────┘
                              ▲                        ▲
                              │                        │
                       ┌─────────────────┐    ┌─────────────────┐
                       │     Qdrant      │    │     Redis       │
                       │  Vector DB      │    │    Cache        │
                       │                 │    │                 │
                       └─────────────────┘    └─────────────────┘
```

## 🚀 Быстрый старт

### 1. Клонируйте репозиторий
```bash
git clone <repository-url>
cd voskhod-1-ai
```

### 2. Настройте переменные окружения
```bash
cp .env.example .env
# Отредактируйте .env файл с вашими ключами
```

### 3. Запустите все сервисы
```bash
docker-compose up -d
```

### 4. Проверьте статус
```bash
# API приложение
curl http://localhost:8000/health

# Документация API
open http://localhost:8000/docs
```

## 📋 Сервисы

### Основные сервисы:
- **api** (FastAPI) - порт 8000
- **postgres** (PostgreSQL) - порт 5432
- **qdrant** (Vector DB) - порт 6333
- **redis** (Cache) - порт 6379

### Опциональные сервисы:
- **telegram_bot** - Telegram бот (запускается отдельно)

## 🛠 Команды управления

```bash
# Запуск всех сервисов
docker-compose up -d

# Запуск только API и баз данных
docker-compose up -d api postgres qdrant redis

# Запуск с телеграм ботом
docker-compose --profile bot up -d

# Просмотр логов
docker-compose logs -f api

# Остановка всех сервисов
docker-compose down

# Остановка с удалением volumes
docker-compose down -v

# Пересборка API
docker-compose build api
```

## 🔧 Конфигурация

### Переменные окружения (.env)

Создайте файл `.env` в корне проекта:

```bash
# Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Базы данных
POSTGRES_USER=voskhod_user
POSTGRES_PASSWORD=voskhod_password
POSTGRES_DB=voskhod_ai

# AI сервисы
OPENROUTER_API_KEY=your_openrouter_key_here

# Ollama для эмбеддингов (бесплатно, локально)
# 1. Установите Ollama: https://ollama.ai/download
# 2. Запустите: ./ollama_setup.sh
# 3. Или вручную:
#    ollama pull nomic-embed-text
#    ollama pull llama3.2
#    ollama serve

# И т.д. (см. .env.example)
```

### Docker Compose файлы

- `docker-compose.yml` - основной конфиг
- `docker-compose.override.yml` - переопределения для разработки

## 🗄 Базы данных

### PostgreSQL
- **База данных**: `voskhod_ai`
- **Пользователь**: `voskhod_user`
- **Пароль**: `voskhod_password`
- **Таблицы**: автоматически создаются при первом запуске

### Qdrant
- **Коллекция**: `university_knowledge`
- **API**: REST на порту 6333
- **Dashboard**: http://localhost:6333/dashboard

### Redis
- **База**: 0 (по умолчанию)
- **Пароль**: нет

## 🔍 Мониторинг и отладка

### Health checks
```bash
# API
curl http://localhost:8000/health

# PostgreSQL
docker-compose exec postgres pg_isready -U voskhod_user -d voskhod_ai

# Qdrant
curl http://localhost:6333/health

# Redis
docker-compose exec redis redis-cli ping
```

### Просмотр логов
```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f api
docker-compose logs -f telegram_bot
```

### Доступ к контейнерам
```bash
# Войти в контейнер API
docker-compose exec api bash

# Войти в PostgreSQL
docker-compose exec postgres psql -U voskhod_user -d voskhod_ai

# Войти в Redis
docker-compose exec redis redis-cli
```

## 🧪 Тестирование API

### Создание API ключа
```bash
curl -X POST "http://localhost:8000/v1/keys" \
  -H "Content-Type: application/json" \
  -d '{"name": "Иван", "surname": "Климов", "role": "user"}'
```

### Получение списка ключей
```bash
curl http://localhost:8000/v1/keys
```

### Тест чата (с API ключом)
```bash
curl -X POST "http://localhost:8000/v1/chat" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question": "Что такое Python?"}'
```

## 🔐 Безопасность

- Все API ключи хранятся в PostgreSQL
- Векторные данные индексируются в Qdrant
- Redis используется для кэширования
- Переменные окружения не коммитятся в Git

## 📊 Масштабирование

### Производственная настройка
```yaml
# В docker-compose.prod.yml
services:
  api:
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 1G
          cpus: '1.0'

  postgres:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2.0'
```

### Балансировка нагрузки
- Используйте Nginx или Traefik для балансировки
- Настройте Redis кластер для высокой доступности
- Масштабируйте Qdrant для больших объемов данных

## 🐛 Устранение неисправностей

### API не запускается
```bash
# Проверьте зависимости
docker-compose build api

# Проверьте логи
docker-compose logs api
```

### База данных недоступна
```bash
# Проверьте статус PostgreSQL
docker-compose ps postgres

# Перезапустите базу
docker-compose restart postgres
```

### Телеграм бот не работает
```bash
# Проверьте токен в .env
# Проверьте логи бота
docker-compose logs telegram_bot
```

## 📚 API Документация

После запуска откройте: http://localhost:8000/docs

## 🤝 Contributing

1. Создайте feature branch
2. Внесите изменения
3. Протестируйте с `docker-compose up`
4. Создайте Pull Request

## 📄 Лицензия

[Укажите лицензию проекта]
