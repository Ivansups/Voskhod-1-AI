#!/usr/bin/env python3
"""
Скрипт для запуска и мониторинга индексации документов с RAG.

Использование:
    python run_indexing.py

Функции:
- Очищает старую векторную базу
- Запускает индексацию всех документов
- Мониторит прогресс в реальном времени
- Показывает итоговую статистику
"""

import time
from typing import Any, Dict

import requests

# Настройки
API_BASE_URL = "http://localhost:8000"
QDRANT_URL = "http://localhost:6333"


def clear_collection() -> bool:
    """Очищает векторную коллекцию."""
    try:
        url = f"{QDRANT_URL}/collections/university_knowledge"
        response = requests.delete(url)
        if response.status_code == 200:
            print("✅ Коллекция очищена")
            return True
        else:
            print(f"❌ Ошибка очистки коллекции: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к Qdrant: {e}")
        return False


def get_indexing_status() -> Dict[str, Any]:
    """Получает статус индексации."""
    try:
        url = f"{API_BASE_URL}/v1/admin/sync/status"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


def monitor_indexing():
    """Мониторит прогресс индексации."""
    print("📊 Мониторинг индексации...")

    start_time = time.time()
    last_progress = -1

    while True:
        status = get_indexing_status()

        if "error" in status:
            print(f"❌ Ошибка получения статуса: {status['error']}")
            time.sleep(10)
            continue

        sync_status = status.get("sync_status", {})

        phase = sync_status.get("phase", "unknown")
        progress = sync_status.get("progress", 0)
        files_processed = sync_status.get("files_processed", 0)
        total_files = sync_status.get("total_files", 0)
        current_file = sync_status.get("current_file", "")

        # Показываем прогресс только при изменении
        if progress != last_progress:
            elapsed = int(time.time() - start_time)
            print(
                f"📈 Прогресс: {progress}% | Файлы: {files_processed}/{total_files} | Время: {elapsed} сек"
            )
            if current_file:
                print(f"📄 Обрабатывается: {current_file}")
            last_progress = progress

        # Проверяем завершение
        if phase == "ready":
            total_time = int(time.time() - start_time)
            documents_count = sync_status.get("documents_count", 0)
            print("\n✅ Индексация завершена!")
            print("📊 Результаты:")
            print(f"   • Время: {total_time} секунд")
            print(f"   • Файлы обработано: {files_processed}/{total_files}")
            print(f"   • Документы в БД: {documents_count}")
            break
        elif phase == "error":
            error_msg = sync_status.get("error_message", "Неизвестная ошибка")
            print(f"\n❌ Ошибка индексации: {error_msg}")
            break

        time.sleep(30)  # Проверяем каждые 30 секунд


def check_collection_stats():
    """Проверяет статистику коллекции."""
    try:
        url = f"{QDRANT_URL}/collections/university_knowledge"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            points_count = data.get("result", {}).get("points_count", 0)
            print(f"📊 Коллекция содержит {points_count} векторов")
            return points_count
        else:
            print(f"❌ Ошибка получения статистики: {response.status_code}")
            return 0
    except Exception as e:
        print(f"❌ Ошибка подключения к Qdrant: {e}")
        return 0


def check_sync_status():
    """Проверяет статус синхронизации."""
    try:
        url = f"{API_BASE_URL}/v1/admin/sync/status"
        response = requests.get(url)
        if response.status_code == 200:
            status = response.json()
            sync_status = status.get("sync_status", {})
            return sync_status
        else:
            print(f"❌ Ошибка получения статуса: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Ошибка подключения к API: {e}")
        return None


def start_indexing(force_reindex=False):
    """Запускает индексацию в фоне."""
    try:
        url = f"{API_BASE_URL}/v1/admin/sync"
        params = {"force": "true"} if force_reindex else {}
        response = requests.post(url, params=params)
        if response.status_code == 200:
            mode = (
                "полной переиндексации"
                if force_reindex
                else "инкрементальной индексации"
            )
            print(f"✅ {mode.capitalize()} запущена в фоне")
            return True
        else:
            print(f"❌ Ошибка запуска индексации: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к API: {e}")
        return False


def main():
    """Основная функция."""
    print("🚀 Запуск индексации документов для RAG системы")
    print("=" * 50)

    # Шаг 1: Проверка текущего статуса
    print("\n1️⃣ Проверка статуса синхронизации...")
    current_status = check_sync_status()

    if current_status:
        phase = current_status.get("phase", "unknown")
        documents_count = current_status.get("documents_count", 0)

        if phase == "ready" and documents_count > 1000:
            print(f"📊 Найдено {documents_count} документов в БД")
            print("🔍 Проверяем необходимость индексации...")

            # Запускаем инкрементальную индексацию
            print("\n2️⃣ Запуск инкрементальной индексации...")
            force_reindex = False
        else:
            print(
                f"⚠️  Система не готова (фаза: {phase}, документов: {documents_count})"
            )
            print("🔄 Будет выполнена полная индексация...")

            # Очищаем коллекцию и делаем полную индексацию
            print("\n2️⃣ Очистка старой коллекции...")
            if not clear_collection():
                print("❌ Невозможно продолжить без очистки коллекции")
                return

            print("\n3️⃣ Запуск полной индексации...")
            force_reindex = True
    else:
        print("❌ Не удалось получить статус, выполняем полную индексацию")

        # Очищаем коллекцию и делаем полную индексацию
        print("\n2️⃣ Очистка старой коллекции...")
        if not clear_collection():
            print("❌ Невозможно продолжить без очистки коллекции")
            return

        print("\n3️⃣ Запуск полной индексации...")
        force_reindex = True

    # Шаг 2/3/4: Запуск индексации
    if not start_indexing(force_reindex):
        print("❌ Невозможно запустить индексацию")
        return

    # Шаг 3/4/5: Мониторинг
    step_num = "4️⃣" if force_reindex else "3️⃣"
    print(f"\n{step_num} Мониторинг процесса...")
    monitor_indexing()

    # Шаг 4/5/6: Финальная проверка
    final_step = "5️⃣" if force_reindex else "4️⃣"
    print(f"\n{final_step} Финальная проверка...")
    time.sleep(5)  # Ждем немного
    vectors_count = check_collection_stats()

    print("\n" + "=" * 50)
    if vectors_count > 1000:
        print("🎉 УСПЕХ! RAG система готова к работе!")
        print("💡 Теперь можно задавать вопросы по учебным материалам")
    else:
        print("⚠️  ВНИМАНИЕ! Количество векторов маловато")
        print("💡 Возможно, некоторые файлы не удалось обработать")
        print("🔄 Попробуйте перезапустить индексацию")


if __name__ == "__main__":
    main()
