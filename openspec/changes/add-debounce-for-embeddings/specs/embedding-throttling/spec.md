## ADDED Requirements

### Requirement: Configurable delay between embedding requests

The embedding service SHALL support a configurable delay (in milliseconds) between consecutive embedding requests. The delay SHALL be applied after each request completes, before the next one starts. The value SHALL be read from `EMBEDDING_DELAY_MS` with provider-specific defaults (0 for OpenAI, 300 for Ollama) when unset.

#### Scenario: Ollama with default delay

- **WHEN** `EMBEDDING_SERVICE=ollama` and `EMBEDDING_DELAY_MS` is not set
- **THEN** a delay of 300 ms is applied between each embedding request

#### Scenario: OpenAI with no delay

- **WHEN** `EMBEDDING_SERVICE=openai` and `EMBEDDING_DELAY_MS` is not set
- **THEN** no delay is applied between embedding requests (0 ms)

#### Scenario: Explicit override

- **WHEN** `EMBEDDING_DELAY_MS=500` is set
- **THEN** a delay of 500 ms is applied between each embedding request regardless of provider

---

### Requirement: Batch size limit for embedding requests

The embedding service SHALL process texts in batches of at most N items, where N is configurable via `EMBEDDING_BATCH_SIZE`. When the number of texts exceeds N, the service SHALL process them in chunks of size N with a delay between each chunk. The default SHALL be 100 for OpenAI (effectively no limit) and 10 for Ollama when unset.

#### Scenario: Ollama processes many chunks in mini-batches

- **WHEN** `embed_batch()` is called with 25 texts and `EMBEDDING_BATCH_SIZE=10`
- **THEN** the service processes 10 texts, then applies delay, then 10 more, then delay, then 5 remaining

#### Scenario: OpenAI processes all at once

- **WHEN** `EMBEDDING_SERVICE=openai` and `embed_batch()` is called with 50 texts
- **THEN** all 50 texts are sent in a single batch (default batch size 100)

---

### Requirement: Delay between files during indexing

The document indexer SHALL support a configurable delay (in milliseconds) between processing consecutive files. The delay SHALL be applied after a file is fully indexed, before starting the next file. The value SHALL be read from `INDEXER_FILE_DELAY_MS` with provider-specific defaults (0 for OpenAI, 1500 for Ollama) when unset.

#### Scenario: Indexer with file delay

- **WHEN** `EMBEDDING_SERVICE=ollama` and indexing processes multiple files
- **THEN** a delay of 1500 ms is applied between completing one file and starting the next (when `INDEXER_FILE_DELAY_MS` is unset)

#### Scenario: Indexer without file delay

- **WHEN** `EMBEDDING_SERVICE=openai` and `INDEXER_FILE_DELAY_MS` is not set
- **THEN** no delay is applied between files (0 ms)
