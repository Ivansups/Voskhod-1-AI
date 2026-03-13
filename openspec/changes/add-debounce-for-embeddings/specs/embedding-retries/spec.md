## ADDED Requirements

### Requirement: Retry only the failed request (per-chunk granularity)

The embedding service SHALL retry only the single embedding request that failed. Retries SHALL NOT apply to the entire batch or to other chunks. When processing a batch of N texts, if chunk K fails after exhausting retries, the service SHALL re-raise immediately. The system SHALL NOT attempt to save partial results: embeddings for chunks 1..K-1 are discarded for that batch; no partial upsert to the vector database SHALL occur. The indexer SHALL treat the entire file as failed and continue with the next file.

#### Scenario: One chunk fails, batch fails

- **WHEN** `embed_batch()` processes 25 chunks and chunk 5 fails after all retries
- **THEN** the service re-raises; no embeddings for that file are upserted to Qdrant

#### Scenario: No partial upsert on failure

- **WHEN** `embed_batch()` has successfully embedded chunks 1-24, and chunk 25 fails after retries
- **THEN** the service re-raises; chunks 1-24 are NOT upserted; the file is treated as fully failed

#### Scenario: Indexer proceeds to next file

- **WHEN** `embed_batch()` fails for a file after retries exhausted
- **THEN** the indexer logs the error, appends to `errors`, and processes the next file; the failed file's chunks are not indexed

---

### Requirement: Retry on transient embedding failures

The embedding service SHALL retry failed embedding requests when the failure is due to a transient error. Transient errors SHALL include: timeout (`httpx.TimeoutException`), connection errors (`httpx.ConnectError`), and HTTP status 5xx or 429. The maximum number of retries SHALL be configurable via `EMBEDDING_MAX_RETRIES` (default: 3 for Ollama, 2 for OpenAI).

#### Scenario: Success after one retry

- **WHEN** an embedding request fails with a timeout, and `EMBEDDING_MAX_RETRIES=3`
- **THEN** the service retries the request; if the retry succeeds, the embedding is returned

#### Scenario: Retries exhausted

- **WHEN** an embedding request fails with a timeout on all retry attempts
- **THEN** the service re-raises the last exception to the caller

#### Scenario: Non-retryable error

- **WHEN** an embedding request fails with HTTP 401 (unauthorized) or 400 (bad request)
- **THEN** the service SHALL NOT retry and SHALL re-raise the exception immediately

---

### Requirement: Exponential backoff between retries

The embedding service SHALL use exponential backoff between retry attempts. The delay before attempt N SHALL be `base_delay_ms * 2^(N-1)`, where `base_delay_ms` is configurable via `EMBEDDING_RETRY_BASE_DELAY_MS` (default: 1000 for Ollama, 500 for OpenAI). The delay SHALL be capped at 30 seconds.

#### Scenario: Backoff progression

- **WHEN** `EMBEDDING_RETRY_BASE_DELAY_MS=1000` and the first attempt fails
- **THEN** the service waits 1000 ms before the first retry, then 2000 ms before the second retry, then 4000 ms before the third retry

#### Scenario: Cap at 30 seconds

- **WHEN** `EMBEDDING_RETRY_BASE_DELAY_MS=10000` and multiple retries occur
- **THEN** no single wait exceeds 30000 ms

---

### Requirement: Indexer continues on embedding failure

When an embedding request fails after exhausting retries, the document indexer SHALL catch the exception, log the error, append it to the result's `errors` list, and continue processing the next file. The indexer SHALL NOT abort the entire indexing run for a single file failure.

#### Scenario: One file fails, others continue

- **WHEN** embedding fails for file B after retries exhausted, and files A, B, C are being indexed
- **THEN** file A is indexed, file B's error is logged and added to `errors`, file C is processed normally
