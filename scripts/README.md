# Скрипты управления системой

Эта папка содержит все скрипты для управления системой Voskhod-1 AI.

## 🚀 Основные скрипты

### `start-with-indexing.sh`
**Полный автоматический запуск системы с индексацией**

```bash
./start-with-indexing.sh
```

- Запускает все сервисы (PostgreSQL, Qdrant, Redis, API)
- Выполняет автоматическую индексацию документов
- Мониторит прогресс в реальном времени
- Делает систему готовой к работе

**Рекомендуется для первого запуска!**

### `docker-indexing.sh`
**Управление индексацией через Docker**

```bash
# Умная индексация (проверяет актуальность данных)
./docker-indexing.sh

# Принудительная полная переиндексация
./docker-indexing.sh force

# Автоматический мониторинг (работает в фоне)
./docker-indexing.sh monitor
```

### `check_indexing_status.sh`
**Проверка статуса индексации**

```bash
./check_indexing_status.sh
```

Показывает текущее состояние системы и рекомендации по дальнейшим действиям.

### `check_config.py`
**Проверка конфигурации**

```bash
python scripts/check_config.py
```

Проверяет переменные окружения и текущие модели.

### `check_rag_data.py`
**Проверка данных RAG**

```bash
python scripts/check_rag_data.py
```

Проверяет данные в Qdrant и тестирует поиск.

## 🛠️ Устаревшие скрипты

### `run_indexing.sh` ⚠️ УСТАРЕЛ
Используйте `./docker-indexing.sh` вместо этого скрипта.

### `run_indexing_force.sh` ⚠️ УСТАРЕЛ
Используйте `./docker-indexing.sh force` вместо этого скрипта.

### `run_indexing.py` ⚠️ УСТАРЕЛ
Теперь индексация работает в контейнере (`server/src/indexer.py`).

## 📁 Структура

```
scripts/
├── README.md                    # Эта документация
├── start-with-indexing.sh       # Полный автоматический запуск
├── docker-indexing.sh           # Управление индексацией
├── check_indexing_status.sh     # Проверка статуса
├── check_config.py              # Проверка конфигурации
├── check_rag_data.py            # Проверка данных RAG
├── run_indexing.sh              # УСТАРЕЛ
├── run_indexing_force.sh        # УСТАРЕЛ
└── run_indexing.py              # УСТАРЕЛ
```

## 🔗 Символические ссылки

Для обратной совместимости в корне проекта созданы символические ссылки на основные скрипты:
- `start-with-indexing.sh` → `scripts/start-with-indexing.sh`
- `docker-indexing.sh` → `scripts/docker-indexing.sh`
- `check_indexing_status.sh` → `scripts/check_indexing_status.sh`