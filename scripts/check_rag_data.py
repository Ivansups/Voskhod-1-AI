#!/usr/bin/env python3
"""Скрипт для проверки данных в RAG системе."""

import asyncio
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "server" / "src"))

from application.services.rag.embedding_service import get_embedding_service


async def check_qdrant_data():
    """Проверяем данные в Qdrant."""
    print("🔍 ПРОВЕРКА ДАННЫХ В QDRANT")

    # Получаем embedding сервис
    embedding_service = get_embedding_service()

    # Генерируем вектор для запроса
    query = "алгоритмы и структуры данных"
    print(f"📝 Запрос: {query}")

    vector = await embedding_service.embed(query)
    print(f"📊 Сгенерирован вектор размером {len(vector)}")

    # Ищем в Qdrant
    qdrant_url = "http://localhost:6333"
    search_url = f"{qdrant_url}/collections/university_knowledge/points/search"

    payload = {"vector": vector, "limit": 5, "with_payload": True, "with_vector": False}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(search_url, json=payload)
            response.raise_for_status()
            result = response.json()

            print("\n📋 НАЙДЕННЫЕ ДОКУМЕНТЫ:")
            for i, hit in enumerate(result.get("result", []), 1):
                score = hit.get("score", 0)
                payload = hit.get("payload", {})

                print(f"\n{i}. Score: {score:.4f}")
                print(f"   Source: {payload.get('source', 'unknown')}")
                print(f"   File: {payload.get('file_path', 'unknown')}")
                print(f"   Content preview: {payload.get('content', '')[:200]}...")

        except Exception as e:
            print(f"❌ Ошибка поиска в Qdrant: {e}")


async def test_specific_queries():
    """Тестируем конкретные запросы на наличие релевантных данных."""
    print("\n🔬 ТЕСТИРОВАНИЕ КОНКРЕТНЫХ ЗАПРОСОВ")

    embedding_service = get_embedding_service()

    queries = [
        "алгоритмы и структуры данных",
        "дискретная математика",
        "математический анализ",
        "программирование",
        "базы данных",
    ]

    for query in queries:
        print(f"\n--- Запрос: {query} ---")

        vector = await embedding_service.embed(query)

        # Ищем в Qdrant
        qdrant_url = "http://localhost:6333"
        search_url = f"{qdrant_url}/collections/university_knowledge/points/search"

        payload = {
            "vector": vector,
            "limit": 3,
            "with_payload": True,
            "with_vector": False,
            "score_threshold": 0.5,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(search_url, json=payload)
                response.raise_for_status()
                result = response.json()

                hits = result.get("result", [])
                print(f"Найдено документов: {len(hits)}")

                if hits:
                    for hit in hits[:2]:  # Показываем только первые 2
                        score = hit.get("score", 0)
                        file_path = hit.get("payload", {}).get("file_path", "")
                        print(f"  • {file_path} (score: {score:.3f})")
                else:
                    print("  ❌ Нет релевантных документов")

            except Exception as e:
                print(f"❌ Ошибка: {e}")


async def test_api_rag_flow():
    """Тестируем полный RAG флоу через API."""
    print("\n🚀 ТЕСТИРОВАНИЕ API RAG ФЛОУ")

    test_questions = [
        "Что изучают на курсе алгоритмов и структур данных?",
        "Расскажи о дискретной математике",
        "Какие темы есть в математическом анализе?",
    ]

    for question in test_questions:
        print(f"\n--- Вопрос: {question} ---")

        # Делаем запрос к API
        api_url = "http://localhost:8000/v1/chat"
        payload = {"question": question, "top_k": 3}

        try:
            response = httpx.post(api_url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()

            answer = result.get("answer", "")
            has_rag = result.get("has_rag_context", False)
            sources = result.get("sources", [])

            print(f"RAG контекст использован: {'✅ ДА' if has_rag else '❌ НЕТ'}")
            print(f"Количество источников: {len(sources)}")

            if sources:
                print("Источники:")
                for source in sources[:2]:
                    file_path = source.get("file_path", "")
                    score = source.get("score", 0)
                    print(f"  • {file_path} (score: {score:.3f})")

            print(f"Ответ: {answer[:200]}...")

        except Exception as e:
            print(f"❌ Ошибка API запроса: {e}")


async def main():
    await check_qdrant_data()
    await test_specific_queries()
    await test_api_rag_flow()


if __name__ == "__main__":
    asyncio.run(main())
