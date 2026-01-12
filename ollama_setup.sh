#!/bin/bash

echo "🚀 Настройка Ollama для бесплатных эмбеддингов"

# Проверяем, установлен ли Ollama
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama не установлен!"
    echo "📥 Скачайте с https://ollama.ai/download"
    echo "💡 Для Mac: brew install ollama"
    echo "💡 Для Linux: curl -fsSL https://ollama.ai/install.sh | sh"
    exit 1
fi

echo "✅ Ollama установлен"

# Проверяем, запущен ли Ollama
if ! pgrep -f "ollama serve" > /dev/null; then
    echo "🔄 Запускаю Ollama..."
    nohup ollama serve > ollama.log 2>&1 &
    sleep 3
fi

echo "✅ Ollama запущен"

# Скачиваем модель эмбеддингов
echo "📥 Скачиваю модель nomic-embed-text..."
ollama pull nomic-embed-text

echo "✅ Модель nomic-embed-text готова!"
echo ""
echo "🎯 Теперь можно запускать систему:"
echo "docker-compose up -d"
echo ""
echo "💰 Всё бесплатно и работает локально!"
