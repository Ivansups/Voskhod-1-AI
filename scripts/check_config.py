#!/usr/bin/env python3
"""Проверка конфигурации системы."""

import os


def check_env_config():
    """Проверяет наличие и корректность переменных окружения."""
    print("🔍 ПРОВЕРКА КОНФИГУРАЦИИ\n")

    required_vars = [
        "TELEGRAM_BOT_TOKEN",
        "OPENROUTER_API_KEY",
        "OPENROUTER_MODEL",
        "OLLAMA_EMBEDDING_MODEL",
        "RAG_TOP_K",
        "RAG_SCORE_THRESHOLD",
    ]

    all_good = True

    for var in required_vars:
        value = os.getenv(var)
        if not value:
            print(f"❌ {var}: НЕ НАСТРОЕН")
            all_good = False
        elif var == "TELEGRAM_BOT_TOKEN" and len(value) < 40:
            print(f"⚠️  {var}: ПОДОЗРИТЕЛЬНО КОРОТКИЙ ТОКЕН")
        elif var == "OPENROUTER_API_KEY" and not value.startswith("sk-or-v1-"):
            print(f"⚠️  {var}: НЕПРАВИЛЬНЫЙ ФОРМАТ КЛЮЧА")
        else:
            if var in ["OPENROUTER_API_KEY"]:
                print(f"✅ {var}: НАСТРОЕН (скрыт)")
            else:
                print(f"✅ {var}: {value}")

    print(f"\n{'🎉 КОНФИГУРАЦИЯ ГОТОВА!' if all_good else '⚠️  ТРЕБУЕТСЯ НАСТРОЙКА'}")

    return all_good


def show_current_models():
    """Показывает текущие модели."""
    print("\n🤖 ТЕКУЩИЕ МОДЕЛИ:")
    print(f"   LLM: {os.getenv('OPENROUTER_MODEL', 'не настроен')}")
    print(f"   Embeddings: {os.getenv('OLLAMA_EMBEDDING_MODEL', 'не настроен')}")
    print(f"   Fallback LLM: {os.getenv('OLLAMA_MODEL', 'не настроен')}")


if __name__ == "__main__":
    check_env_config()
    show_current_models()
