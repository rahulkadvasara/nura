# RAG Performance Optimization & Reliability

This document outlines the performance optimization and reliability enhancements built into the Nura Retrieval-Augmented Generation (RAG) platform.

## 1. RAG Cache Layer

To minimize downstream latency and reduce LLM API overhead costs, a multi-stage in-memory caching architecture has been implemented.

### Cache Subsystems
1. **Query Intent Cache**: Caches deterministic classifications (e.g. `medical_question`, `report_analysis`) mapping directly to query semantic signatures.
2. **Embedding Cache**: Maps raw text chunks to 1024-dimensional HuggingFace vector embeddings.
3. **Retrieval Cache**: Caches multi-collection nearest-neighbor search results using a serialized parameters hash key.
4. **Context Assembly Cache**: Prevents repetitive prompt generation by caching constructed context profiles.

### Configurations
Caches use in-memory dictionaries with explicit Time-To-Live (TTL) checks:
- `QUERY_CACHE_TTL`: 1800 seconds (30 mins)
- `EMBEDDING_CACHE_TTL`: 86400 seconds (24 hours)
- `RETRIEVAL_CACHE_TTL`: 300 seconds (5 mins)
- `CONTEXT_CACHE_TTL`: 120 seconds (2 mins)

Cache metrics trackers log hit/miss ratios, visible dynamically on the administrator dashboard.

---

## 2. Concurrency & Parallel Retrieval

Multi-collection retrieval searches are executed concurrently to prevent serialization bottlenecks:
- **Bounded Concurrency**: Implemented using `asyncio.Semaphore(3)` to cap concurrent search requests to Qdrant.
- **Timeout Controls**: A configurable timeout of `2.0` seconds ensures slow semantic lookups are aborted, falling back to clean merges rather than locking up thread queues.

---

## 3. Circuit Breaker Pattern

External API endpoints and critical subsystems are wrapped with stateful Circuit Breakers to guarantee fault tolerance:
- **Groq LLM Api**: Tripped on 5 consecutive network or server failures. Falls back to mock completions containing helpful diagnostic notifications.
- **Embedding Service**: Falls back to dummy 1024d zero-vectors to prevent indexing or retrieval blockages.
- **Qdrant Vector Database**: Falls back to empty list results to allow other sources (e.g., MongoDB longitudinal records) to compile successfully.

### Circuit Breaker States
- **CLOSED**: Service operates normally.
- **OPEN**: Service has failed repeatedly. Upstream requests are blocked automatically and fallback values are returned immediately.
- **HALF_OPEN**: Cooldown period (30.0s) has elapsed. The next request acts as a trial to check if service availability has resumed.
