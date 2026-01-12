#!/usr/bin/env python3
"""Тестовый скрипт для проверки флоу работы LLM и RAG сервисов."""

import asyncio
import sys
import os

# Добавляем путь к исходному коду
sys.path.append('/Users/ivanklimov/Documents/GitHub/Voskhod-1-AI/server/src')

from application.services.llm.llm_manager import get_llm_service, reset_llm_service
from application.services.rag.embedding_service import get_embedding_service
from application.infrastructure.vector_db.qdrant_client import QdrantClient
from application.services.rag.retriever import RAGRetriever
from application.services.rag.engine import RAGEngine


async def test_llm_init():
    """Тестируем инициализацию LLM сервиса."""
    print("=== ТЕСТИРОВАНИЕ ИНИЦИАЛИЗАЦИИ LLM СЕРВИСА ===")

    try:
        llm_service = get_llm_service()
        print("✅ LLM сервис инициализирован успешно")
        print(f"   Тип сервиса: {type(llm_service).__name__}")
        print(f"   Модель: {llm_service.model}")
        print(f"   Температура: {llm_service.temperature}")
        print(f"   Max tokens: {llm_service.max_tokens}")
        return llm_service
    except Exception as e:
        print(f"❌ Ошибка инициализации LLM сервиса: {e}")
        return None


async def test_embedding_init():
    """Тестируем инициализацию embedding сервиса."""
    print("\n=== ТЕСТИРОВАНИЕ ИНИЦИАЛИЗАЦИИ EMBEDDING СЕРВИСА ===")

    try:
        embedding_service = get_embedding_service()
        print("✅ Embedding сервис инициализирован успешно")
        print(f"   Тип сервиса: {type(embedding_service).__name__}")
        print(f"   Размерность вектора: {embedding_service.get_vector_size()}")
        return embedding_service
    except Exception as e:
        print(f"❌ Ошибка инициализации embedding сервиса: {e}")
        return None


async def test_qdrant_init():
    """Тестируем инициализацию Qdrant клиента."""
    print("\n=== ТЕСТИРОВАНИЕ ИНИЦИАЛИЗАЦИИ QDRANT КЛИЕНТА ===")

    try:
        qdrant_client = QdrantClient()
        print("✅ Qdrant клиент инициализирован успешно")
        print(f"   URL: {qdrant_client.url}")
        print(f"   Коллекция: {qdrant_client.collection_name}")

        # Проверяем подключение
        collections = await qdrant_client.list_collections()
        print(f"   Доступные коллекции: {len(collections.get('result', {}).get('collections', []))}")

        return qdrant_client
    except Exception as e:
        print(f"❌ Ошибка инициализации Qdrant клиента: {e}")
        return None


async def test_retriever_init(qdrant_client, embedding_service):
    """Тестируем инициализацию RAG retriever."""
    print("\n=== ТЕСТИРОВАНИЕ ИНИЦИАЛИЗАЦИИ RAG RETRIEVER ===")

    if not qdrant_client or not embedding_service:
        print("❌ Пропускаем тест retriever - нет зависимостей")
        return None

    try:
        retriever = RAGRetriever(
            qdrant_client=qdrant_client,
            embedding_service=embedding_service
        )
        print("✅ RAG retriever инициализирован успешно")
        print(f"   Top K: {retriever.top_k}")
        print(f"   Score threshold: {retriever.score_threshold}")
        return retriever
    except Exception as e:
        print(f"❌ Ошибка инициализации RAG retriever: {e}")
        return None


async def test_rag_engine_init(retriever, llm_service):
    """Тестируем инициализацию RAG engine."""
    print("\n=== ТЕСТИРОВАНИЕ ИНИЦИАЛИЗАЦИИ RAG ENGINE ===")

    if not retriever or not llm_service:
        print("❌ Пропускаем тест RAG engine - нет зависимостей")
        return None

    try:
        rag_engine = RAGEngine(retriever=retriever, llm_service=llm_service)
        print("✅ RAG engine инициализирован успешно")
        return rag_engine
    except Exception as e:
        print(f"❌ Ошибка инициализации RAG engine: {e}")
        return None


async def test_llm_basic(llm_service):
    """Тестируем базовую генерацию ответа через LLM."""
    print("\n=== ТЕСТИРОВАНИЕ БАЗОВОЙ ГЕНЕРАЦИИ ОТВЕТА ===")

    if not llm_service:
        print("❌ Пропускаем тест - нет LLM сервиса")
        return False

    try:
        question = "Что такое искусственный интеллект?"
        print(f"Вопрос: {question}")

        result = llm_service.generate_answer_with_rag(question, return_json=True)
        print("✅ Ответ сгенерирован успешно")
        print(f"   Длина ответа: {len(result.get('answer', ''))} символов")
        print(f"   RAG контекст использован: {result.get('has_rag_context', False)}")
        print(f"   Ответ (первые 100 символов): {result.get('answer', '')[:100]}...")

        return True
    except Exception as e:
        print(f"❌ Ошибка генерации ответа: {e}")
        return False


async def test_rag_flow(rag_engine):
    """Тестируем полный RAG флоу."""
    print("\n=== ТЕСТИРОВАНИЕ RAG ФЛОУ ===")

    if not rag_engine:
        print("❌ Пропускаем тест - нет RAG engine")
        return False

    try:
        question = "Что изучают на курсе алгоритмов и структур данных?"
        print(f"Вопрос: {question}")

        result = await rag_engine.query(question, return_json=True)
        print("✅ RAG запрос выполнен успешно")
        print(f"   Длина ответа: {len(result.get('answer', ''))} символов")
        print(f"   RAG контекст использован: {result.get('has_rag_context', False)}")
        print(f"   Количество источников: {len(result.get('sources', []))}")

        if result.get('sources'):
            print("   Источники:")
            for i, source in enumerate(result.get('sources', [])[:2]):  # Показываем первые 2
                print(f"     {i+1}. {source.get('file_path', 'unknown')} (score: {source.get('score', 0):.3f})")

        return True
    except Exception as e:
        print(f"❌ Ошибка RAG флоу: {e}")
        return False


async def main():
    """Главная функция тестирования."""
    print("🚀 НАЧИНАЕМ ТЕСТИРОВАНИЕ ФЛОУ РАБОТЫ LLM И RAG СЕРВИСОВ\n")

    # Сбрасываем глобальный LLM сервис для чистого теста
    reset_llm_service()

    # Тестируем инициализацию компонентов
    llm_service = await test_llm_init()
    embedding_service = await test_embedding_init()
    qdrant_client = await test_qdrant_init()
    retriever = await test_retriever_init(qdrant_client, embedding_service)
    rag_engine = await test_rag_engine_init(retriever, llm_service)

    # Тестируем функциональность
    basic_llm_ok = await test_llm_basic(llm_service)
    rag_flow_ok = await test_rag_flow(rag_engine)

    # Закрываем соединения
    if qdrant_client:
        await qdrant_client.close()
    if embedding_service and hasattr(embedding_service, 'close'):
        await embedding_service.close()

    print("\n" + "="*60)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")

    results = {
        "LLM инициализация": llm_service is not None,
        "Embedding инициализация": embedding_service is not None,
        "Qdrant инициализация": qdrant_client is not None,
        "Retriever инициализация": retriever is not None,
        "RAG Engine инициализация": rag_engine is not None,
        "Базовая LLM генерация": basic_llm_ok,
        "RAG флоу": rag_flow_ok,
    }

    for test_name, passed in results.items():
        status = "✅ ПРОШЕЛ" if passed else "❌ ПРОВАЛЕН"
        print(f"   {test_name}: {status}")

    total_passed = sum(results.values())
    total_tests = len(results)

    print(f"\n🎯 ИТОГО: {total_passed}/{total_tests} тестов пройдено")

    if total_passed == total_tests:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
    else:
        print("⚠️  НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ")


if __name__ == "__main__":
    asyncio.run(main())