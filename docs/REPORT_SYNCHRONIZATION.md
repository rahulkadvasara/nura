# Knowledge Synchronization Pipeline

This document details the architecture, schemas, and processing flow for Phase 11 - Sprint 5: Knowledge Synchronization Pipeline.

## 1. Architectural Synchronization Flow

```text
Processed Report
        │
        ▼
Validation (Completed extraction & AI summary check)
        │
        ▼
ReportPatientMemoryBuilder
  - Query existing PatientMemory MongoDB document
  - Add active parameters, medications history, diagnoses, summaries, risks, and recommendations
  - Chronological sorting
  - Update MongoDB (summary_version increment)
        │
        ▼
ReportChunkBuilder
  - Generate semantic statement text chunks (AI summary, lab findings, recommendations)
  - Prevent raw OCR indexing
        │
        ▼
EmbeddingService (1536-dim vectors generation)
        │
        ▼
Qdrant patient_reports Collection
  - scroll and compare version/hash
  - upsert new points with metadata
        │
        ▼
SyncValidator (Post-sync validation checks)
        │
        ▼
Complete
```

---

## 2. MongoDB `patient_memory` updates

We incrementally update the `patient_memory` MongoDB collection with chronological tracking:
- **`longitudinal_summary`**: Updated baseline AI patient summaries.
- **`latest_report_summary`**: The AI summary text from the most recently synchronized report.
- **`latest_risk`**: Overall risk and score classification.
- **`laboratory_history`**: Chronological array listing test values, reference limits, and status flags.
- **`medication_history`**: Chronological list of medications prescribed.
- **`diagnosis_history`**: List of clinical diagnoses.
- **`laboratory_trends`**: Synthesized textual trends tracker.
- **`latest_recommendations`**: Clinical action items list.
- **`timeline`**: Diagnostic events timeline log.

---

## 3. Qdrant `patient_reports` metadata

Every vector point upserted to Qdrant contains the following payload fields:
- `patient_id` (str): reference patient ID
- `report_id` (str): reference report ID
- `document_type` (str): category type (e.g. `blood_test`, `prescription`)
- `report_date` (str): timestamp date ISO
- `section` (str): chunk origin section (e.g. `laboratory_results`, `recommendations`)
- `source` (str): `"patient_reports"`
- `indexed_at` (str): current timestamp
- `embedding_version` (str): active model version
- `content_hash` (str): chunks MD5 signature

---

## 4. Chunk Builder Strategy

To maintain clean semantic context without noise:
- **Do NOT index raw OCR text** (due to parser inaccuracies and spelling issues).
- **Executive Summaries**: Grouped as semantic summary blocks.
- **Structured Laboratory Results**: Described as statements: `f"Laboratory Test Parameter: {name} is {val} {unit} (Reference limit: {ref}, status: {status})"`
- **Diagnoses**: Described as `f"Clinical Diagnosis: {diag}"`
- **Recommendations**: Formatted as action items.

---

## 5. Incremental & Rollback Controls

- **Content Hashing**: Checked on scroll to bypass unnecessary vector recalculations.
- **Validation Audit**: Validates MongoDB records and vector counts match expected, raising rollback errors on database failures.
