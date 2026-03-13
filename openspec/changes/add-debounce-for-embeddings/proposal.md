# Proposal: Add Debounce and Retries for Embeddings

## Why

When indexing documents with Ollama as the embedding provider, the indexer sends many sequential embedding requests without any throttling. Ollama (especially `nomic-embed-text` running locally) cannot handle rapid-fire requests — GPU/CPU gets saturated, leading to timeouts, connection errors, or overload. A single file with 50 chunks triggers 50 back-to-back HTTP calls; there is no delay between chunks or between files. Additionally, transient failures (network blips, Ollama restart, memory pressure) cause the entire indexing run to fail with no recovery.

## What Changes

- **Throttling for embedding requests**:
  - Configurable delay between embedding requests (or between mini-batches)
  - Configurable delay between files during indexing
  - Optional batch size limit: process chunks in small batches (e.g., 5–10) with a pause between batches
  - Applies primarily to Ollama; OpenAI can use defaults that effectively disable throttling

- **Retry logic for failed embeddings**:
  - Retry with exponential backoff when an embedding request fails (timeout, 5xx, connection error)
  - Configurable max retries and base delay
  - After exhausting retries, fail the current file/chunk and continue with the next (or abort, configurable)

- **Configuration via environment**:
  - `EMBEDDING_DELAY_MS` — delay between embedding requests (default: 0 for OpenAI, 300 for Ollama)
  - `EMBEDDING_BATCH_SIZE` — max chunks per batch before pause (default: 10 for Ollama)
  - `EMBEDDING_MAX_RETRIES` — max retries per request (default: 3)
  - `EMBEDDING_RETRY_BASE_DELAY_MS` — base delay for exponential backoff (default: 1000)
  - `INDEXER_FILE_DELAY_MS` — delay between files (default: 1500)

- **No breaking changes**: Existing behavior preserved when new env vars are unset (sensible defaults per provider).

## Capabilities

### New Capabilities

- `embedding-throttling`: Configurable delays between embedding requests and between files during indexing. Batch size limits and provider-specific defaults (Ollama vs OpenAI).

- `embedding-retries`: Retry with exponential backoff when embedding requests fail. Configurable retry count and base delay. Graceful degradation (skip/continue vs abort).

### Modified Capabilities

- _(none — no existing specs in openspec/specs/)_

## Impact

- **`server/src/application/services/rag/embedding_service.py`**: Add delay and retry logic to `OllamaEmbeddingService.embed()` and `embed_batch()`. Consider Ollama batch API with small batches.
- **`server/src/application/services/git_sync/indexer.py`**: Add delay between files in `index_directory()`; optionally split chunks into batches with pauses.
- **`server/src/application/core/config.py`**: Add new settings for `EMBEDDING_DELAY_MS`, `EMBEDDING_BATCH_SIZE`, `EMBEDDING_MAX_RETRIES`, `EMBEDDING_RETRY_BASE_DELAY_MS`, `INDEXER_FILE_DELAY_MS`.
- **`.env.example`**: Document new variables with recommended values for Ollama.
