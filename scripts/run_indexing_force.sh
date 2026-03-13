#!/bin/bash

# Скрипт для ПРИНУДИТЕЛЬНОЙ полной переиндексации RAG системы
# Всегда очищает коллекцию и индексирует заново

echo "🔄 ПРИНУДИТЕЛЬНАЯ полная переиндексация RAG системы"
echo "=================================================="
echo "⚠️  ВНИМАНИЕ: Все существующие вектора будут удалены!"
echo ""

read -p "Вы уверены, что хотите продолжить? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Операция отменена"
    exit 1
fi

# Настройки
API_BASE_URL="http://localhost:8000"
QDRANT_URL="http://localhost:6333"

echo ""
echo "1️⃣ Очистка коллекции..."
curl -s -X DELETE "$QDRANT_URL/collections/university_knowledge" > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Коллекция очищена"
else
    echo "❌ Ошибка очистки коллекции"
    exit 1
fi

echo ""
echo "2️⃣ Запуск полной индексации..."
response=$(curl -s -X POST "$API_BASE_URL/v1/admin/sync?force=true")
if echo "$response" | grep -q "running"; then
    echo "✅ Полная индексация запущена в фоне"
else
    echo "❌ Ошибка запуска индексации:"
    echo "$response"
    exit 1
fi

echo ""
echo "3️⃣ Мониторинг процесса..."
echo "📊 Мониторинг индексации..."

start_time=$(date +%s)
last_progress=-1

while true; do
    status=$(curl -s "$API_BASE_URL/v1/admin/sync/status")

    if ! echo "$status" | jq . > /dev/null 2>&1; then
        echo "❌ Ошибка получения статуса"
        sleep 10
        continue
    fi

    phase=$(echo "$status" | jq -r '.sync_status.phase')
    progress=$(echo "$status" | jq -r '.sync_status.progress')
    files_processed=$(echo "$status" | jq -r '.sync_status.files_processed')
    total_files=$(echo "$status" | jq -r '.sync_status.total_files')
    current_file=$(echo "$status" | jq -r '.sync_status.current_file')

    # Показываем прогресс только при изменении
    if [ "$progress" != "$last_progress" ]; then
        current_time=$(date +%s)
        elapsed=$((current_time - start_time))
        echo "📈 Прогресс: ${progress}% | Файлы: ${files_processed}/${total_files} | Время: ${elapsed} сек"
        if [ "$current_file" != "null" ] && [ -n "$current_file" ]; then
            echo "📄 Обрабатывается: $current_file"
        fi
        last_progress=$progress
    fi

    # Проверяем завершение
    if [ "$phase" = "ready" ]; then
        total_time=$(date +%s)
        total_time=$((total_time - start_time))
        documents_count=$(echo "$status" | jq -r '.sync_status.documents_count')
        echo ""
        echo "✅ Полная индексация завершена!"
        echo "📊 Результаты:"
        echo "   • Время: $total_time секунд"
        echo "   • Файлы обработано: ${files_processed}/${total_files}"
        echo "   • Документы в БД: $documents_count"
        break
    elif [ "$phase" = "error" ]; then
        error_msg=$(echo "$status" | jq -r '.sync_status.error_message')
        echo ""
        echo "❌ Ошибка индексации: $error_msg"
        break
    fi

    sleep 30  # Проверяем каждые 30 секунд
done

echo ""
echo "4️⃣ Финальная проверка..."
sleep 5

vectors_count=$(curl -s "$QDRANT_URL/collections/university_knowledge" | jq -r '.result.points_count' 2>/dev/null || echo "0")
echo "📊 Коллекция содержит $vectors_count векторов"

echo ""
echo "=================================================="
if [ "$vectors_count" -gt 1000 ]; then
    echo "🎉 УСПЕХ! RAG система готова к работе!"
    echo "💡 Теперь можно задавать вопросы по учебным материалам"
else
    echo "⚠️  ВНИМАНИЕ! Количество векторов маловато"
    echo "💡 Возможно, некоторые файлы не удалось обработать"
    echo "🔄 Попробуйте перезапустить индексацию"
fi