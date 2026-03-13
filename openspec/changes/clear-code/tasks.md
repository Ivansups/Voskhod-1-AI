## 1. Ruff Setup

- [x] 1.1 Add ruff to dev dependencies in pyproject.toml; remove black and isort
- [x] 1.2 Add [tool.ruff] and [tool.ruff.format] to pyproject.toml (line-length 88, exclude __pycache__, .venv, .git)
- [x] 1.3 Enable rule sets E, F, I at minimum
- [x] 1.4 Run `poetry install` and verify `ruff check .` and `ruff format .` work

## 2. Initial Lint and Format Pass

- [x] 2.1 Run `ruff format .` and fix any formatting issues
- [x] 2.2 Run `ruff check .` and fix critical issues (F401 unused imports, etc.); document any remaining excluded rules

## 3. Api Block Cleanup

- [x] 3.1 Remove unused imports and dead code from server/src/application/api/
- [x] 3.2 Simplify handlers where logic is convoluted; extract helpers if needed
- [x] 3.3 Ensure `ruff check server/src/application/api/` passes

## 4. Services Block Cleanup

- [x] 4.1 Remove unused imports and dead code from server/src/application/services/
- [x] 4.2 Apply DRY where same logic is duplicated across llm, rag, telegram, key_generator
- [x] 4.3 Ensure `ruff check server/src/application/services/` passes

## 5. Infrastructure Block Cleanup

- [x] 5.1 Remove unused imports and dead code from server/src/application/infrastructure/
- [x] 5.2 Simplify parsers and qdrant client if needed
- [x] 5.3 Ensure `ruff check server/src/application/infrastructure/` passes

## 6. Scripts Block Cleanup

- [x] 6.1 Run ruff on scripts/ Python files; fix issues
- [x] 6.2 Remove deprecated scripts (run_indexing_simple.sh, etc.) if no longer used; update scripts/README.md
- [x] 6.3 Ensure `ruff check scripts/` passes

## 7. Orphan and Duplicate Files

- [x] 7.1 Check if server/src/test_flow.py is used; remove if unused
- [x] 7.2 Check if server/src/indexer.py duplicates git_sync/indexer.py; remove duplicate if so
- [x] 7.3 Remove unused dependencies from pyproject.toml if any identified

## 8. Project Root Organization

- [x] 8.1 Create docs/ and move INDEXING_README.md into docs/
- [x] 8.2 Update README.md links to point to docs/INDEXING_README.md
- [x] 8.3 Move check_config.py and check_rag_data.py to scripts/ or justify keeping in root
- [x] 8.4 Verify symlinks (check_indexing_status.sh, docker-indexing.sh, start-with-indexing.sh) point to scripts/
- [x] 8.5 Decide on plans/ placement (keep or move to docs/plans/); document in README if needed

## 9. Documentation

- [x] 9.1 Add ruff commands to README or CONTRIBUTING: `ruff check .`, `ruff format .`
- [x] 9.2 Update any affected docs for new file locations (e.g. INDEXING_README paths)
