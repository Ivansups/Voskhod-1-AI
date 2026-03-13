#!/bin/bash

# Скрипт для запуска всех сервисов с автоматической индексацией
# Запускает систему и сразу начинает индексацию документов

set -e

echo "🚀 Запуск Voskhod AI с автоматической индексацией"
echo "=================================================="

# Проверяем наличие docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose не найден"
    exit 1
fi

# Функция для проверки статуса сервиса
check_service_status() {
    local service=$1
    local max_attempts=60
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

echo ""
echo "1️⃣ Запуск основных сервисов..."

# Запускаем основные сервисы
docker-compose up -d postgres qdrant redis

# Ждем их запуска
check_service_status "postgres"
check_service_status "qdrant"
check_service_status "redis"

echo ""
echo "2️⃣ Запуск API сервиса..."
docker-compose up -d api
check_service_status "api"

echo ""
echo "3️⃣ Запуск автоматической индексации..."
export INDEXER_MODE=once
docker-compose --profile auto-indexer up -d indexer

echo ""
echo "4️⃣ Мониторинг индексации..."

# Мониторим индексацию
max_wait=1800  # 30 минут максимум
elapsed=0

while [ $elapsed -lt $max_wait ]; do
    if command -v curl &> /dev/null; then
        status_response=$(curl -s http://localhost:8000/v1/admin/sync/status 2>/dev/null || echo "error")
        if [ "$status_response" != "error" ]; then
            phase=$(echo "$status_response" | jq -r '.sync_status.phase' 2>/dev/null || echo "unknown")
            progress=$(echo "$status_response" | jq -r '.sync_status.progress' 2>/dev/null || echo "0")
            documents_count=$(echo "$status_response" | jq -r '.sync_status.documents_count' 2>/dev/null || echo "0")
            files_processed=$(echo "$status_response" | jq -r '.sync_status.files_processed' 2>/dev/null || echo "0")
            total_files=$(echo "$status_response" | jq -r '.sync_status.total_files' 2>/dev/null || echo "0")

            echo "📊 Прогресс: ${progress}% | Файлы: ${files_processed}/${total_files} | Документы: $documents_count | Фаза: $phase"

            if [ "$phase" = "ready" ]; then
                echo ""
                echo "✅ Индексация завершена!"
                break
            fi
        fi
    fi

    sleep 10
    elapsed=$((elapsed + 10))
done

if [ $elapsed -ge $max_wait ]; then
    echo ""
    echo "⚠️  Превышено время ожидания индексации"
    echo "💡 Индексация может продолжаться в фоне"
fi

echo ""
echo "5️⃣ Финальная проверка..."

# Проверяем итоговое состояние
if command -v curl &> /dev/null; then
    sleep 5
    status_response=$(curl -s http://localhost:8000/v1/admin/sync/status 2>/dev/null || echo "error")
    if [ "$status_response" != "error" ]; then
        phase=$(echo "$status_response" | jq -r '.sync_status.phase' 2>/dev/null || echo "unknown")
        documents_count=$(echo "$status_response" | jq -r '.sync_status.documents_count' 2>/dev/null || echo "0")

        echo "📊 Финальный статус:"
        echo "   • Фаза: $phase"
        echo "   • Документов в БД: $documents_count"

        if [ "$phase" = "ready" ] && [ "$documents_count" -gt 1000 ]; then
            echo "🎉 Система полностью готова к работе!"
            echo "💡 Теперь можно задавать вопросы по учебным материалам"
        else
            echo "⚠️  Проверьте логи для диагностики проблем"
            echo "🔍 Логи API: docker-compose logs api"
            echo "🔍 Логи индексатора: docker-compose --profile auto-indexer logs indexer"
        fi
    fi
fi

echo ""
echo "6️⃣ Запуск телеграм бота (опционально)..."
read -p "Запустить телеграм бота? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker-compose up -d telegram_bot
    echo "✅ Телеграм бот запущен"
fi

echo ""
echo "=================================================="
echo "🚀 Voskhod AI готов к работе!"
echo ""
echo "📋 Управление:"
echo "   • Остановить все: docker-compose down"
echo "   • Логи API: docker-compose logs api"
echo "   • Логи индексатора: docker-compose --profile auto-indexer logs indexer"
echo "   • Переиндексация: ./docker-indexing.sh force"
echo ""
echo "🌐 Доступ:"
echo "   • API: http://localhost:8000"
echo "   • Qdrant: http://localhost:6333"
echo "   • Redis: localhost:6379"