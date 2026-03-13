## ADDED Requirements

### Requirement: Ruff as single linter and formatter

The project SHALL use Ruff for both static analysis (lint) and code formatting. Ruff MUST replace black and isort. Configuration MUST reside in `pyproject.toml` under `[tool.ruff]` and `[tool.ruff.format]`.

#### Scenario: Ruff runs successfully

- **WHEN** developer runs `ruff check .` from project root
- **THEN** Ruff reports lint issues (if any) for Python files in `server/` and `scripts/`

#### Scenario: Ruff format applies style

- **WHEN** developer runs `ruff format .` from project root
- **THEN** Python files are reformatted according to configured rules

#### Scenario: Exclusions apply

- **WHEN** Ruff scans the project
- **THEN** `__pycache__`, `.venv`, `.git`, and build artifacts are excluded from checks

### Requirement: Unified configuration for server and scripts

Ruff configuration SHALL apply to both `server/` and `scripts/` directories. One config file (pyproject.toml) MUST govern all Python code.

#### Scenario: Scripts are linted

- **WHEN** developer runs `ruff check scripts/`
- **THEN** Python scripts in `scripts/` are checked with the same rules as server code

#### Scenario: Line length and rule set

- **WHEN** configuration is read
- **THEN** default line length is 88 (or project standard); rule sets include E (errors), F (Pyflakes), I (isort) at minimum

### Requirement: Dev dependencies updated

`pyproject.toml` dev dependencies SHALL include `ruff`. Black and isort SHALL be removed from dev dependencies. mypy MAY remain optional.

#### Scenario: Ruff installable

- **WHEN** developer runs `poetry install --with dev`
- **THEN** Ruff is installed and available as `ruff`

#### Scenario: Black and isort removed

- **WHEN** developer inspects dev dependencies
- **THEN** black and isort are not listed
