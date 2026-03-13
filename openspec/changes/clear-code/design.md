# Design: Clear Code (Чистка кода)

## Context

Проект Voskhod-1-AI: FastAPI backend, RAG (LlamaIndex, Qdrant), Telegram bot, git sync + indexing. Структура: `server/src/application/` (api, services, infrastructure, domain), `scripts/` (indexing, shell). Black и mypy есть в dev-deps, но конфигурация отсутствует, линтер не запускается. В коде накапливаются unused imports, дублирование, закомментированный код.

**Constraints:**
- Не менять публичное API и поведение
- Не перегружать рефакторинг — достаточно держать код читаемым и поддерживаемым
- Pre-commit не использовать (ручной запуск линтера при необходимости)

## Goals / Non-Goals

**Goals:**
- Настроить Ruff как единый линтер (lint + format), заменить black/isort
- Удалить мёртвый код: unused imports, функции, модули, неиспользуемые deps
- Упростить логику, снизить дублирование (DRY)
- Соблюдать SOLID умеренно: чёткие границы модулей, один класс — одна зона ответственности, без излишней абстракции

**Non-Goals:**
- Pre-commit hooks
- CI-интеграция (оставить на потом)
- Глубокий рефакторинг архитектуры
- Полное соответствие SOLID «до последней буквы»

## Decisions

### 1. Ruff вместо black/isort/mypy

**Decision:** Ruff как единственный инструмент для lint и format.

**Rationale:** Ruff покрывает flake8, isort, частично mypy; быстрее, один конфиг. Для текущего размера проекта достаточно. mypy можно оставить опционально для типов, но не блокирующим.

**Alternative:** Оставить black + isort + mypy. Отклонено — три конфига, медленнее, избыточно для начала.

### 2. SOLID: умеренное применение

**Decision:** Придерживаться принципов там, где это естественно и не усложняет код.

- **S (SRP):** Класс/модуль — одна зона ответственности. Не разбивать на микроклассы ради «чистоты».
- **O (OCP):** Избегать жёстких switch/cascade if, где легко расширить через новый handler/provider. Не вводить абстракции «на будущее».
- **D (DIP):** Зависимости через конструктор/DI уже есть (FastAPI Depends). Не усложнять.
- **I, L:** Практически не трогать — интерфейсы и иерархии не перестраивать.

**Rationale:** Цель — чистота и читаемость, а не «идеальный» SOLID. Переусложнение вредит.

### 3. Области чистки (по блокам)

| Блок | Фокус |
|------|--------|
| `api/` | Unused imports, упрощение handlers, единый стиль ответов |
| `services/` (llm, rag, telegram, key_generator) | DRY, вынос повторяющейся логики, удаление мёртвого кода |
| `infrastructure/` | Упрощение парсеров и qdrant-клиента |
| `scripts/` | Python: lint; shell: форматирование, удаление мёртвых веток |

### 4. Дубликаты и orphan-файлы

**Decision:** `server/src/indexer.py` и `server/src/test_flow.py` — проверить использование. Если `indexer` дублирует `services/git_sync/indexer.py`, удалить корневой. `test_flow.py` — удалить, если не используется.

**Rationale:** Меньше путаницы, один источник правды.

### 4a. Организация корня проекта

**Decision:** Корень — только entrypoints и топ-конфиг. Остальное — по папкам.

| Место | Содержимое |
|-------|------------|
| Корень | `README.md`, `pyproject.toml`, `docker-compose*.yml`, `run_telegram_bot.py`, `Makefile`, `.env*`, symlinks на `scripts/` |
| `docs/` | `INDEXING_README.md`, другая расширенная документация (при необходимости) |
| `scripts/` | Все shell- и Python-скрипты; deprecated — удалить или пометить |
| `plans/` | Планы, архитектурные заметки (оставить как есть или перенести в `docs/plans/`) |

**Rationale:** Корень не раздувается, документация и скрипты логично сгруппированы.

### 5. Конфигурация Ruff

**Decision:** `pyproject.toml` → `[tool.ruff]`, `[tool.ruff.format]`. Один конфиг для `server/` и `scripts/`. Исключения: `__pycache__`, `.venv`, миграции (если появятся).

**Rationale:** Централизованная конфигурация, стандарт для Poetry-проектов.

### 6. Зависимости

**Decision:** Убрать black, isort из dev-deps; добавить ruff. mypy — оставить опционально, не в default dev-group.

**Rationale:** Ruff заменяет black и isort. mypy можно вернуть позже для строгой проверки типов.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Ruff-правила слишком строгие | Начать с базового набора (E, F, I); добавлять W по мере необходимости |
| Рефакторинг сломает поведение | Только удаление мёртвого кода и упрощение; логику не менять без тестов |
| Ruff vs mypy — дублирование проверок | Ruff проверяет типы поверхностно; для строгих типов оставить mypy отдельно |

## Migration Plan

1. Добавить Ruff в dev-deps, убрать black/isort.
2. Создать `[tool.ruff]` в `pyproject.toml`.
3. Запустить `ruff check .` и `ruff format .`, исправить критичные замечания.
4. По блокам: api → services → infrastructure → scripts — удалить dead code, упростить логику.
5. Проверить и удалить orphan-файлы (`test_flow.py`, корневой `indexer.py` при дублировании).
6. Организовать корень: `docs/` для INDEXING_README и др.; скрипты в `scripts/`; deprecated — удалить.
7. Обновить README/CONTRIBUTING с инструкцией по запуску `ruff check` и `ruff format`.

**Rollback:** Revert коммитов; поведение не менялось, откат безопасен.

## Open Questions

- Нужен ли `ruff --fix` в CI позже? Defer.
- Оставлять ли mypy в dev-deps для опциональной проверки? Решить при реализации.
