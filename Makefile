# Makefile для управления Voskhod AI проектом

.PHONY: help build up down restart logs clean test

# По умолчанию показать помощь
help:
	@echo "Доступные команды:"
	@echo "  build        - Собрать все Docker образы"
	@echo "  up           - Запустить все сервисы"
	@echo "  up-api       - Запустить только API и базы данных"
	@echo "  up-bot       - Запустить с телеграм ботом"
	@echo "  down         - Остановить все сервисы"
	@echo "  restart      - Перезапустить все сервисы"
	@echo "  logs         - Просмотреть логи всех сервисов"
	@echo "  logs-api     - Просмотреть логи API"
	@echo "  logs-bot     - Просмотреть логи бота"
	@echo "  clean        - Остановить и удалить все контейнеры и volumes"
	@echo "  shell-api    - Войти в shell API контейнера"
	@echo "  shell-db     - Войти в PostgreSQL shell"
	@echo "  test-api     - Протестировать API endpoints"
	@echo "  migrate      - Запустить миграции базы данных"

# Сборка образов
build:
	docker-compose build

# Запуск сервисов
up:
	docker-compose up -d

up-api:
	docker-compose up -d api postgres qdrant redis

up-bot:
	docker-compose --profile bot up -d

# Остановка сервисов
down:
	docker-compose down

# Перезапуск
restart:
	docker-compose restart

# Логи
logs:
	docker-compose logs -f

logs-api:
	docker-compose logs -f api

logs-bot:
	docker-compose logs -f telegram_bot

# Очистка
clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

# Shell доступ
shell-api:
	docker-compose exec api bash

shell-db:
	docker-compose exec postgres psql -U voskhod_user -d voskhod_ai

# Тестирование
test-api:
	@echo "Тестирование API..."
	@curl -s http://localhost:8000/health | grep -q "ok" && echo "✅ API health check passed" || echo "❌ API health check failed"
	@sleep 1
	@docker-compose exec -T postgres pg_isready -U voskhod_user -d voskhod_ai > /dev/null 2>&1 && echo "✅ PostgreSQL is ready" || echo "❌ PostgreSQL is not ready"
	@sleep 1
	@curl -s http://localhost:6333/health | grep -q "true" && echo "✅ Qdrant is ready" || echo "❌ Qdrant is not ready"
	@sleep 1
	@docker-compose exec -T redis redis-cli ping | grep -q "PONG" && echo "✅ Redis is ready" || echo "❌ Redis is not ready"

# Миграции (если будут использоваться Alembic)
migrate:
	@echo "Миграции базы данных..."
	# docker-compose exec api alembic upgrade head

# Быстрая проверка всех сервисов
status:
	@echo "=== Статус сервисов ==="
	@docker-compose ps
	@echo ""
	@echo "=== Health checks ==="
	@$(MAKE) test-api
