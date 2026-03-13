#!/bin/bash

# Скрипт для запуска индексации через Docker контейнеры
# Заменяет внешние скрипты run_indexing.sh

set -e

echo "🐳 Запуск индексации через Docker контейнер"
echo "==========================================="

# Проверяем наличие docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose не найден"
    exit 1
fi

# Функция для проверки статуса сервиса
check_service_status() {
    local service=$1
    local max_attempts=30
    local attempt=1

    echo "🔍 Проверка статуса сервиса $service..."

    while [ $attempt -le $max_attempts ]; do
        if docker-compose ps $service | grep -q "Up"; then
            echo "✅ Сервис $service запущен"
            return 0
        fi

        echo "⏳ Ожидание запуска сервиса $service (попытка $attempt/$max_attempts)..."
        sleep 2
        ((attempt++))
    done

    echo "❌ Сервис $service не запустился"
    return 1
}

# Определяем режим индексации
MODE=${1:-once}

case $MODE in
    "once")
        echo "📄 Режим: Одноразовая индексация"
        export INDEXER_MODE=once
        ;;
    "force")
        echo "💪 Режим: Принудительная полная индексация"
        export INDEXER_MODE=force
        ;;
    "monitor")
        echo "🔄 Режим: Автоматический мониторинг"
        export INDEXER_MODE=monitor
        ;;
    *)
        echo "❌ Неизвестный режим: $MODE"
        echo "💡 Используйте: once (по умолчанию), force, или monitor"
        exit 1
        ;;
esac

echo ""
echo "1️⃣ Проверка основных сервисов..."

# Проверяем, что основные сервисы запущены
check_service_status "postgres"
check_service_status "qdrant"
check_service_status "redis"
check_service_status "api"

echo ""
echo "2️⃣ Запуск индексации..."

# Запускаем сервис индексации
if [ "$MODE" = "monitor" ]; then
    echo "🔄 Запуск сервиса мониторинга (работает в фоне)..."
    docker-compose --profile indexer up -d indexer
    echo "✅ Сервис индексации запущен в фоне"
    echo "💡 Остановить: docker-compose --profile indexer down indexer"
else
    echo "📊 Запуск одноразовой индексации..."
    docker-compose --profile indexer run --rm indexer
    echo "✅ Индексация завершена"
fi

echo ""
echo "3️⃣ Проверка результатов..."

# Ждем немного и проверяем статус через API
sleep 3

echo "🔍 Проверка статуса через API..."
if command -v curl &> /dev/null; then
    status_response=$(curl -s http://localhost:8000/v1/admin/sync/status 2>/dev/null || echo "error")
    if [ "$status_response" != "error" ]; then
        phase=$(echo "$status_response" | jq -r '.sync_status.phase' 2>/dev/null || echo "unknown")
        documents_count=$(echo "$status_response" | jq -r '.sync_status.documents_count' 2>/dev/null || echo "0")

        echo "📊 Текущий статус:"
        echo "   • Фаза: $phase"
        echo "   • Документов в БД: $documents_count"

        if [ "$phase" = "ready" ] && [ "$documents_count" -gt 1000 ]; then
            echo "🎉 Система готова к работе!"
        elif [ "$MODE" != "monitor" ]; then
            echo "⚠️  Проверьте логи контейнера для деталей"
        fi
    else
        echo "⚠️  API недоступен, проверьте логи контейнеров"
    fi
else
    echo "⚠️  curl не найден, пропускаем проверку API"
fi

echo ""
echo "==========================================="
if [ "$MODE" = "monitor" ]; then
    echo "📡 Сервис индексации работает в фоне"
    echo "🔍 Мониторить: docker-compose --profile indexer logs -f indexer"
    echo "🛑 Остановить: docker-compose --profile indexer down"
else
    echo "✅ Индексация завершена!"
fi