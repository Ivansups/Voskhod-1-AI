#!/bin/bash

# Скрипт для проверки статуса индексации RAG системы
# Использует curl для получения информации о состоянии

echo "🔍 Проверка статуса индексации RAG системы"
echo "==========================================="

# Настройки
API_BASE_URL="http://localhost:8000"
QDRANT_URL="http://localhost:6333"

echo ""
echo "1️⃣ Проверка статуса синхронизации..."
status_response=$(curl -s "$API_BASE_URL/v1/admin/sync/status")

if echo "$status_response" | jq . > /dev/null 2>&1; then
    phase=$(echo "$status_response" | jq -r '.sync_status.phase')
    progress=$(echo "$status_response" | jq -r '.sync_status.progress')
    documents_count=$(echo "$status_response" | jq -r '.sync_status.documents_count')
    files_processed=$(echo "$status_response" | jq -r '.sync_status.files_processed')
    total_files=$(echo "$status_response" | jq -r '.sync_status.total_files')
    current_file=$(echo "$status_response" | jq -r '.sync_status.current_file')
    last_sync=$(echo "$status_response" | jq -r '.sync_status.last_sync_time')

    echo "📊 Статус синхронизации:"
    echo "   • Фаза: $phase"
    echo "   • Прогресс: ${progress}%"
    echo "   • Документов в БД: $documents_count"
    echo "   • Файлов обработано: $files_processed/$total_files"

    if [ "$current_file" != "null" ] && [ -n "$current_file" ]; then
        echo "   • Текущий файл: $current_file"
    fi

    if [ "$last_sync" != "null" ] && [ -n "$last_sync" ]; then
        echo "   • Последняя синхронизация: $last_sync"
    fi
else
    echo "❌ Не удалось получить статус синхронизации"
    echo "💡 Возможно, API сервер не запущен"
fi

echo ""
echo "2️⃣ Проверка коллекции Qdrant..."
vectors_response=$(curl -s "$QDRANT_URL/collections/university_knowledge")

if echo "$vectors_response" | jq . > /dev/null 2>&1; then
    vectors_count=$(echo "$vectors_response" | jq -r '.result.points_count' 2>/dev/null || echo "0")
    echo "📊 Коллекция содержит $vectors_count векторов"
else
    echo "❌ Не удалось получить информацию о коллекции"
    echo "💡 Возможно, Qdrant не запущен"
fi

echo ""
echo "3️⃣ Рекомендации:"
if [ "$phase" = "ready" ] && [ "$documents_count" -gt 1000 ]; then
    echo "✅ Система готова к работе!"
    echo "💡 Данные актуальные, индексация не требуется"
    echo "🔄 При следующем запуске будет выполнена инкрементальная индексация"
elif [ "$phase" = "running" ] || [ "$phase" = "indexing" ]; then
    echo "⏳ Индексация выполняется..."
    echo "💡 Подождите завершения процесса"
elif [ "$vectors_count" -gt 0 ]; then
    echo "⚠️  Данные есть, но статус неизвестен"
    echo "💡 Возможно, процесс индексации был прерван"
    echo "🔄 Рекомендуется перезапустить индексацию"
else
    echo "🚀 Необходимо выполнить начальную индексацию"
    echo "💡 Запустите: ./docker-indexing.sh"
fi

echo ""
echo "==========================================="