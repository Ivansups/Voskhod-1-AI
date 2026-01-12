#!/usr/bin/env python3
"""Проверка используемого LLM сервиса."""

import sys
sys.path.append('/Users/ivanklimov/Documents/GitHub/Voskhod-1-AI/server/src')

from application.services.llm.llm_manager import get_llm_service

def test_llm_service():
    """Проверяем, какой LLM сервис используется."""
    try:
        service = get_llm_service()
        print(f"✅ Используется сервис: {type(service).__name__}")
        print(f"   Модель: {getattr(service, 'model', 'неизвестна')}")

        # Проверяем, что это OpenRouter
        if "OpenRouter" in type(service).__name__:
            print("🎯 OpenRouter выбран как основной сервис!")
        elif "Ollama" in type(service).__name__:
            print("⚠️  Используется Ollama (fallback)")

    except Exception as e:
        print(f"❌ Ошибка инициализации сервиса: {e}")

if __name__ == "__main__":
    test_llm_service()