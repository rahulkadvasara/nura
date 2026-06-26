# RAG Production Architecture

This document describes Nura's production Retrieval-Augmented Generation (RAG) architecture.

## 1. System Topology & Pipeline Flow

The E2E RAG retrieval and processing workflow operates as follows:

```
[Query Input] 
      │
      ▼
[Intent Detection & Classifier] ──(Cache Match?)──► [Return Intent from Cache]
      │ (Miss)
      ▼
[Embedding Generation Service]  ──(Cache Match?)──► [Return Vector from Cache]
      │ (Miss)
      ▼
[Parallel Multi-Collection Search] ──(Cache Match?)──► [Return Results from Cache]
      │ (Miss)
      ├─ Qdrant Search: patient_memory (Bounded Concurrency & Timeout)
      ├─ Qdrant Search: patient_reports
      └─ Qdrant Search: medical_knowledge
      │
      ▼
[Concurrency Merging & Re-ranking]
      │
      ▼
[Context Assembly & Token Budgeting] ──(Cache Match?)──► [Return Context from Cache]
      │ (Miss)
      ▼
[Groq LLM Generation] ──(Circuit Breaker Guard)──► [Structured UI Response]
```

---

## 2. Multi-Stage Optimization Layer

1. **Subsystem Isolation**: Every upstream integration (Groq API, Qdrant search, local embeddings) is protected by isolated in-memory caches and stateful circuit breakers.
2. **Deterministic Fallbacks**: If upstream components trip, clean fallbacks (mock response files, zero vector spaces, empty index search listings) are returned immediately to prevent total application lock-up.
3. **Structured Logging & Telemetry**: Every search, embedding generation, context build, and intent classification records metrics, compilable dynamically under `rag_monitoring_service` for system analysis.

---

## 3. RAG Quality Evaluation Harness

A programmatic evaluation framework has been added to continuously evaluate retrieval quality against precision, recall, citation accuracy, duplication rate, and context utilization:
- **Automatic Evaluations**: Every custom query search has telemetry calculated and logged to MongoDB (`rag_evaluations` collection).
- **Benchmark Suite**: Runs 28 automated queries covering all 7 medical intents. Compiled categories metrics are saved to MongoDB (`rag_benchmarks` collection) and can be triggered/exported via the RAG dashboard.
