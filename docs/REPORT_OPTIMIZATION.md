# Report Processing Optimization Guide

## Overview

The Nura Report Analysis subsystem is production-optimized for scalability, fault-tolerance, and efficiency. This document covers the worker architecture, queue lifecycle, cache strategy, retry strategy, parallel execution, performance tuning, and monitoring metrics.

---

## 1. Worker Architecture

### Worker Pool

The background processing system uses an async worker pool managed by `WorkerScheduler`. Each `BackgroundWorker` is an independent `asyncio.Task` that:

1. Polls `ReportQueueManager` for the next available job (priority-ordered)
2. Delegates execution to the existing `PipelineService` orchestrator
3. Updates `ReportProgressTracker` at each stage milestone
4. Records heartbeats to MongoDB (`worker_heartbeats` collection) every 10 seconds

```
WorkerScheduler
    │
    ├── BackgroundWorker #1 ──► QueueManager (dequeue) ──► PipelineService ──► ProgressTracker
    ├── BackgroundWorker #2 ──► ...
    └── BackgroundWorker #3 ──► ...
```

### Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `REPORT_WORKER_COUNT` | `3` | Number of concurrent background workers |

### Auto-Resume on Restart

On startup, `WorkerScheduler.start()` calls `recover_stale_processing_jobs()` which re-queues any jobs that were stuck in `PROCESSING` state (e.g., due to a crash) for longer than 30 minutes.

### Graceful Shutdown

Shutdown sets an `asyncio.Event`. Workers finish their current job before exiting. The scheduler waits up to 60 seconds for all workers to complete.

---

## 2. Queue Lifecycle

Jobs transition through the following states:

```
PENDING → QUEUED → PROCESSING → COMPLETED
                              ↓
                            FAILED (< max_retries) → QUEUED (retry)
                              ↓
                            DEAD_LETTER (≥ max_retries)
```

| Status | Description |
|--------|-------------|
| `PENDING` | Created but not yet queued for processing |
| `QUEUED` | Waiting in the priority queue |
| `PROCESSING` | Claimed by a worker |
| `COMPLETED` | Successfully processed |
| `FAILED` | Processing failed (will retry if below max_retries) |
| `CANCELLED` | Manually cancelled before processing |
| `DEAD_LETTER` | Permanently failed — max retries exhausted |

### Priority Levels

| Priority | Use Case |
|----------|----------|
| `HIGH` | Admin-triggered re-processing |
| `NORMAL` | Standard patient upload |
| `LOW` | Background re-index |

Jobs are dequeued by `priority_order ASC, created_at ASC` — highest priority first, FIFO within the same priority level.

---

## 3. Cache Strategy

Three dedicated caches are implemented in `ReportCacheService`:

### OCR Cache
- **Key**: SHA-256 of file bytes (content-addressable)
- **TTL**: 24 hours
- **Purpose**: Skip OCR re-processing when the same file is re-uploaded
- **Invalidation**: Cleared when `invalidate_report(report_id)` is called

### Embedding Cache
- **Key**: SHA-256 of text chunk content
- **TTL**: 12 hours
- **Purpose**: Reuse embeddings across re-synchronization runs
- **Invalidation**: Cleared with `invalidate_report(report_id)` for all chunks associated with that report

### Summary Cache
- **Key**: `{report_id}::v{version}`
- **TTL**: 6 hours
- **Purpose**: Skip AI API calls when report content hasn't changed
- **Invalidation**: All version entries for the report cleared on invalidation

### When to Invalidate

Call `cache_service.invalidate_report(report_id)` when:
- A report file is re-uploaded
- Force-retry pipeline is triggered with new content
- Report is deleted

---

## 4. Retry Strategy

### Per-Stage Retries (PipelineService)

Each pipeline stage (OCR, extraction, risk, summary, sync) retries up to `max_stage_retries` times with exponential backoff:

```
Attempt 1 → fail → wait 1s
Attempt 2 → fail → wait 2s
Attempt 3 → fail → STAGE_FAILED
```

### Queue-Level Retries (QueueManager)

When a job fails (whole pipeline), `mark_failed()` re-queues it up to `max_retries` (default: 3) times:

```
Job Attempt 1 → fail → retry_count=1 → re-queued
Job Attempt 2 → fail → retry_count=2 → re-queued
Job Attempt 3 → fail → retry_count=3 → DEAD_LETTER
```

### Dead-Letter Queue

Permanently failed jobs in `DEAD_LETTER` status are visible in:
- Admin dashboard → System Health → Failures tab
- API: `GET /reports/system/queue` → `recent_failures`
- MongoDB `report_jobs` collection (status: `dead_letter`)

---

## 5. Parallel Execution

### Parallel Page OCR (`ParallelOCRProcessor`)

For large documents (100+ pages), pages are processed in parallel:

```python
processor = ParallelOCRProcessor(max_concurrency=4)
results = await processor.process_pages_parallel(page_coroutines)
```

- Bounded by `asyncio.Semaphore(max_concurrency=4)`
- Failed pages return exceptions — processing continues for remaining pages
- Results returned in original order

### Parallel Chunk Embedding (`ParallelEmbeddingProcessor`)

Text chunks are embedded concurrently with cache integration:

```python
processor = ParallelEmbeddingProcessor(
    embedding_service=...,
    max_concurrency=8,
    cache_service=...
)
vectors = await processor.embed_chunks(text_chunks)
```

### Batched Qdrant Upserts (`BatchQdrantUpserter`)

Points are grouped into batches before upserting:

```python
upserter = BatchQdrantUpserter(vector_service=..., batch_size=50)
result = await upserter.upsert_batched("patient_reports", points)
```

- Default batch size: **50 points**
- Failures in one batch do not abort subsequent batches

---

## 6. Progress Tracking

Each report has a real-time progress record in `report_progress` MongoDB collection:

| Stage | Percentage |
|-------|-----------|
| `uploaded` | 5% |
| `ocr` | 30% |
| `extraction` | 50% |
| `risk` | 65% |
| `summary` | 85% |
| `sync` | 95% |
| `completed` | 100% |

**Frontend polling**: Patient dashboard polls `GET /reports/{id}/progress` every 3 seconds and renders an animated progress bar with the current stage label.

---

## 7. Performance Tuning

### Recommended Worker Counts

| Environment | Workers | Notes |
|-------------|---------|-------|
| Development | 1–2 | Low throughput needed |
| Staging | 3 | Default |
| Production (low) | 3–5 | Up to ~30 reports/hour |
| Production (high) | 8–12 | With scaled MongoDB & Qdrant |

### Cache TTL Recommendations

| Cache | Low Latency Priority | Storage Priority |
|-------|---------------------|-----------------|
| OCR | 48h | 12h |
| Embedding | 24h | 6h |
| Summary | 12h | 3h |

### Queue Backlog Alert Threshold

Monitor: if `queued + pending > (worker_count × 10)`, consider scaling workers or alerting ops.

---

## 8. Monitoring Metrics

All metrics are available via:

- **Admin Dashboard**: `/dashboard/admin/reports` → System Health Monitor
- **API endpoints**:
  - `GET /reports/system/health` — overall health summary
  - `GET /reports/system/workers` — worker pool + heartbeats
  - `GET /reports/system/queue` — queue depth per status
  - `GET /reports/system/cache` — hit ratios + cache sizes

### Available Metrics

| Metric | Source | Endpoint |
|--------|--------|----------|
| Reports / hour | BackgroundTelemetry | `/system/health` |
| Failure rate % | BackgroundTelemetry | `/system/health` |
| Active / idle workers | WorkerScheduler | `/system/workers` |
| Worker heartbeats | MongoDB `worker_heartbeats` | `/system/workers` |
| Queue depth by status | MongoDB `report_jobs` | `/system/queue` |
| DLQ jobs | MongoDB `report_jobs` | `/system/queue` |
| OCR cache hit ratio | BackgroundTelemetry | `/system/cache` |
| Embedding cache hit ratio | BackgroundTelemetry | `/system/cache` |
| Summary cache hit ratio | BackgroundTelemetry | `/system/cache` |
| Avg queue wait time | BackgroundTelemetry | `/system/health` |
| Worker utilization % | BackgroundTelemetry | `/system/health` |
| Total reports processed | BackgroundTelemetry | `/system/health` |
| Avg pages per report | BackgroundTelemetry | `/system/health` |
