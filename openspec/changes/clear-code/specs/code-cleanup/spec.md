## ADDED Requirements

### Requirement: Remove dead code

The codebase SHALL have no unused imports, functions, classes, or modules. Commented-out code blocks SHALL be removed. Unused dependencies in `pyproject.toml` SHALL be identified and removed.

#### Scenario: No unused imports

- **WHEN** Ruff runs with rule F401 (unused import) enabled
- **THEN** no Python file contains unused imports, or they are explicitly excluded with justification

#### Scenario: Orphan and duplicate files resolved

- **WHEN** implementation is complete
- **THEN** `server/src/test_flow.py` is removed if unused; `server/src/indexer.py` is removed if it duplicates `application/services/git_sync/indexer.py`

### Requirement: Logic simplification and DRY

Code in `api/`, `services/`, and `infrastructure/` SHALL be simplified: reduce nested conditionals, extract repeated logic, improve readability. SOLID principles SHALL be applied moderately—no over-abstraction.

#### Scenario: Handlers are readable

- **WHEN** developer reads an API route handler
- **THEN** logic is clear; complex branching is extracted to helper functions where appropriate

#### Scenario: No gratuitous duplication

- **WHEN** same logic appears in multiple modules
- **THEN** it is extracted to a shared function or utility unless extraction would reduce clarity

### Requirement: Project root organization

Files in the project root SHALL be organized. Documentation, scripts, and configuration MUST have clear placement. Root SHALL contain only essential entrypoints and top-level config.

#### Scenario: Documentation placement

- **WHEN** project structure is finalized
- **THEN** extended documentation (e.g. `INDEXING_README.md`) is placed in `docs/` or clearly linked from main `README.md`; `README.md` remains in root as main entry

#### Scenario: Scripts consolidated

- **WHEN** project structure is finalized
- **THEN** Python utility scripts (`check_config.py`, `check_rag_data.py`) are either in `scripts/` or justified in root; entrypoints like `run_telegram_bot.py` MAY remain in root

#### Scenario: Symlinks and deprecated scripts

- **WHEN** scripts are organized
- **THEN** symlinks in root (`check_indexing_status.sh`, `docker-indexing.sh`, `start-with-indexing.sh`) point to `scripts/`; deprecated scripts in `scripts/` (e.g. `run_indexing_simple.sh`) are removed or archived if no longer used

#### Scenario: Plans and design docs

- **WHEN** project structure is finalized
- **THEN** `plans/` directory (or equivalent) contains planning/design documents; structure is documented in README or CONTRIBUTING

### Requirement: Per-block cleanup order

Cleanup SHALL proceed by block: `api/` → `services/` → `infrastructure/` → `scripts/` → root. Each block SHALL be lint-clean and free of dead code before moving to the next.

#### Scenario: Api block clean

- **WHEN** api block cleanup is done
- **THEN** `ruff check server/src/application/api/` passes; handlers follow consistent style

#### Scenario: Services block clean

- **WHEN** services block cleanup is done
- **THEN** `ruff check server/src/application/services/` passes; DRY applied where obvious
