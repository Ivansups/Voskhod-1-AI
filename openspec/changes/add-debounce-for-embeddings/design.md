# Design: Embedding Throttling and Retries

## Context

The document indexer processes files sequentially. For each file, it parses content into chunks (max 1500 chars each), then calls `embedding_service.embed_batch(texts)`. `OllamaEmbeddingService.embed_batch()` iterates over texts and calls `embed()` once per chunk — no batching, no delay, no retry. When Ollama is overloaded or a transient error occurs, the entire indexing run fails.

**Current flow:**
```
index_directory() → for each file → _process_and_index_file() → _index_chunks() → embed_batch(texts)
                                                                                      ↓
                                                    for text in texts: embed(text)  [no delay, no retry]
```

**Constraints:**
- Must remain compatible with both Ollama and OpenAI embedding services.
- No breaking changes: unset env vars → sensible provider-specific defaults.
- Indexer and embedding service live in separate modules; throttling/retry logic should be cohesive.

## Goals / Non-Goals

**Goals:**
- Prevent Ollama overload by introducing configurable delays between embedding requests and between files.
- Recover from transient failures (timeout, 5xx, connection reset) via retries with exponential backoff.
- Keep configuration simple: env vars with clear defaults per provider.

**Non-Goals:**
- Changing chunking strategy or chunk size.
- Adding new embedding providers.
- Real-time rate limiting for chat/RAG queries (only indexing is affected).

## Decisions

### 1. Where to implement throttling

**Decision:** Throttling (delay between requests, batch size) in `EmbeddingService` (Ollama implementation); file-level delay in `DocumentIndexer`.

**Rationale:** Embedding service owns the HTTP boundary to Ollama — per-request delay belongs there. File-level delay is indexing-specific and belongs in the indexer.

**Alternative considered:** Put all throttling in the indexer. Rejected because the indexer would need to know about batch boundaries and call `embed_batch` in chunks; that couples indexing to embedding internals.

### 2. Where to implement retries

**Decision:** Retries inside `EmbeddingService.embed()` (and thus applied to each call from `embed_batch`).

**Rationale:** Retries are a cross-cutting concern at the HTTP boundary. Single place to handle timeouts, 5xx, connection errors. Both `embed()` and `embed_batch()` benefit without duplication.

**Alternative considered:** Retries in the indexer. Rejected because other callers of embedding service (e.g., future streaming indexer) would not get retries.

### 3. Ollama: batch API vs sequential with delay

**Decision:** Start with sequential calls + delay. Optionally support Ollama batch API (`input` as array) with small batches (≤10) in a follow-up if needed.

**Rationale:** Current Ollama API uses `prompt` for single text. Batch API uses `input` (array). There is a known quality degradation for batch size > 16. Sequential + delay is simpler, predictable, and solves the overload problem. Batch API can be added later if we need to optimize latency.

### 4. Retry strategy

**Decision:** Exponential backoff: delay = `base_delay_ms * 2^attempt` (capped at e.g. 30s). Retry on: `httpx.TimeoutException`, `httpx.HTTPStatusError` for 5xx and 429, `httpx.ConnectError`.

**Rationale:** Standard pattern for transient failures. 429 (rate limit) explicitly included for future-proofing.

### 5. Behavior after retries exhausted

**Decision:** Re-raise the last exception. Indexer catches it, logs error, appends to `errors` list, continues with next file.

**Rationale:** Proposal allows "skip/continue vs abort" — continue is safer for long runs. One bad file should not stop the whole indexing.

### 6. Provider-specific defaults

**Decision:** Defaults applied in `config.py` based on `EMBEDDING_SERVICE`:

| Var | OpenAI default | Ollama default |
|-----|----------------|----------------|
| EMBEDDING_DELAY_MS | 0 | 300 |
| EMBEDDING_BATCH_SIZE | 100 (no practical limit) | 10 |
| EMBEDDING_MAX_RETRIES | 2 | 3 |
| EMBEDDING_RETRY_BASE_DELAY_MS | 500 | 1000 |
| INDEXER_FILE_DELAY_MS | 0 | 1500 |

**Rationale:** OpenAI handles load well; Ollama needs throttling. Explicit env override always wins.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Indexing becomes much slower | Delay values are configurable; users can tune for their hardware. Defaults are conservative. |
| Retries mask persistent failures | Log each retry attempt; after final failure, error is surfaced and file is skipped. |
| Config drift (env vars forgotten) | Document in `.env.example` with comments. |
| OpenAI gets throttling by mistake | Default 0 delay for OpenAI; only Ollama gets non-zero by default. |

## Migration Plan

1. Add new settings to `config.py` with provider-based defaults.
2. Implement throttling and retries in `OllamaEmbeddingService`; add file delay in indexer.
3. Update `.env.example` with new variables and recommended values.
4. No DB or API contract changes — no migration script.
5. **Rollback:** Revert code; old behavior returns. Env vars can remain (no effect if code doesn't read them).

## Open Questions

- Should we add a `INDEXER_ABORT_ON_ERROR` (or similar) flag to stop indexing on first file failure instead of continuing? Defer to implementation phase.
- Ollama batch API: worth implementing now for latency, or wait for user feedback? Defer.
