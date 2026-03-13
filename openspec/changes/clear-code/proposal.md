# Proposal: Clear Code (Чистка кода)

## Why

Кодовая база растёт, в разных модулях (API, services, infrastructure, scripts) накапливаются неиспользуемые импорты, мёртвый код и запутанная логика. Black и mypy есть в dev-зависимостях, но линтер не настроен и не интегрирован в процесс разработки. Без единого стандарта и автоматических проверок качество кода деградирует, что усложняет поддержку и развитие проекта.

## What Changes

- **Настройка линтера и tooling**:
  - Выбор и настройка линтера (Ruff — единый инструмент для lint и format)
  - Конфигурация для server и scripts
  - Ручной запуск (`ruff check`, `ruff format`); pre-commit не используется

- **Удаление мёртвого кода**:
  - Неиспользуемые импорты, функции, классы, модули
  - Зависимости в `pyproject.toml`, которые больше не используются
  - Удаление закомментированного кода и неиспользуемых файлов (например `test_flow.py`, `indexer.py` в корне `server/src` при дублировании в services)

- **Чистка логики**:
  - Упрощение условной логики и циклов
  - Снижение дублирования (DRY)
  - Улучшение структуры в каждом блоке: `api/`, `services/`, `infrastructure/`, `scripts/`

- **No breaking changes**: Изменения касаются внутренней структуры и качества кода, публичные API и поведение сохраняются.

## Capabilities

### New Capabilities

- `linting-setup`: Конфигурация Ruff (lint + format), правила для server и scripts. Единый стандарт без pre-commit.

- `code-cleanup`: Удаление мёртвого кода (unused imports, functions, modules) и рефакторинг логики (упрощение, DRY, улучшение структуры) по блокам: api, services, infrastructure, scripts.

### Modified Capabilities

- _(none — openspec/specs/ пуст)_

## Impact

- **`pyproject.toml`**: Ruff вместо black/isort. Конфигурация `[tool.ruff]`.
- **`server/src/`**: Чистка в `application/api/`, `application/services/`, `application/infrastructure/`, `application/domain/`. Удаление или перемещение `test_flow.py`, `indexer.py` при дублировании.
- **`scripts/`**: Чистка shell- и Python-скриптов.
- **Корень проекта**: Организация — `docs/` для расширенной документации (INDEXING_README и др.), скрипты в `scripts/`, deprecated — удалить. Entrypoints (`run_telegram_bot.py`) в корне. `check_config.py`, `check_rag_data.py` — в `scripts/` или обосновать наличие в корне.
