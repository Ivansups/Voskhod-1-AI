## 1. Configuration

- [x] 1.1 Add new settings to `config.py`: `EMBEDDING_DELAY_MS`, `EMBEDDING_BATCH_SIZE`, `EMBEDDING_MAX_RETRIES`, `EMBEDDING_RETRY_BASE_DELAY_MS`, `INDEXER_FILE_DELAY_MS` with provider-specific defaults (Ollama vs OpenAI)
- [x] 1.2 Add or update `.env.example` with new variables and recommended values for Ollama

## 2. Embedding Service — Retries

- [x] 2.1 Wrap `OllamaEmbeddingService.embed()` HTTP call in retry loop with exponential backoff (`base_delay * 2^attempt`, cap 30s)
- [x] 2.2 Retry on `httpx.TimeoutException`, `httpx.ConnectError`, `httpx.HTTPStatusError` for 5xx and 429
- [x] 2.3 Do not retry on 4xx (except 429); re-raise immediately
- [x] 2.4 Log each retry attempt with attempt number and exception

## 3. Embedding Service — Throttling

- [x] 3.1 Add `asyncio.sleep(EMBEDDING_DELAY_MS / 1000)` after each `embed()` call in `embed_batch()` (skip when 0)
- [x] 3.2 Split `embed_batch()` into mini-batches of `EMBEDDING_BATCH_SIZE`; apply delay between batches when processing more than batch_size texts
- [x] 3.3 Ensure `OpenAIEmbeddingService` remains unchanged (no throttling by default)

## 4. Indexer — File Delay and Error Handling

- [x] 4.1 Add `asyncio.sleep(INDEXER_FILE_DELAY_MS / 1000)` after each file in `index_directory()` (skip when 0)
- [x] 4.2 Verify `_process_and_index_file` exceptions are caught, logged, appended to `errors`, and indexing continues with next file (already present; confirm behavior)
