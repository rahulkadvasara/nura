# Report Processing Pipeline Orchestrator

The Nura Report Processing Pipeline coordinates clinical ingestion, OCR processing, structured data extraction, clinical risk scoring, AI summarization, and vector database synchronization into a single, cohesive, transaction-safe workflow.

---

## 1. System Architecture

The pipeline orchestrator acts as a single-entry controller (`PipelineService`) coordinating multiple autonomous micro-services.

```mermaid
sequenceDiagram
    autonumber
    actor User as Patient/Admin
    participant API as Reports Router
    participant Service as PipelineService
    participant OCR as OCRService
    participant Extractor as ExtractionService
    participant Risk as RiskAnalysisService
    participant AI as ReportUnderstandingService
    participant Sync as ReportSyncService
    participant DB as MongoDB / Qdrant

    User->>API: Upload Report (PDF/Image)
    API->>DB: Ingest UPLOADED report record
    API-->>User: Success Response (Async process queued)
    API->>Service: execute_pipeline(report_id)
    
    rect rgb(240, 248, 255)
        note right of Service: Stage 1: OCR Scan
        Service->>OCR: process_report(report_id)
        OCR-->>Service: ocr_status = completed
    end
    
    rect rgb(240, 255, 240)
        note right of Service: Stage 2: Clinical Extraction
        Service->>Extractor: extract_medical_information(report_id)
        Extractor-->>Service: extraction_status = completed
    end

    rect rgb(255, 245, 230)
        note right of Service: Stage 3: Risk Engine
        Service->>Risk: analyze_report_risks(report_id)
        Risk-->>Service: overall_risk & risk_score updated
    end

    rect rgb(255, 240, 245)
        note right of Service: Stage 4: AI Summary
        Service->>AI: generate_report_summary(report_id)
        AI-->>Service: ai_summary & doctor_summary updated
    end

    rect rgb(240, 240, 240)
        note right of Service: Stage 5: DB & Vector Sync
        Service->>Sync: synchronize_report(report_id)
        Sync-->>Service: is_synchronized = true
    end

    Service->>DB: Update pipeline_status = READY
```

---

## 2. Pipeline Status Lifecycle

Reports progress through the following status states during execution:

* **`UPLOADED`**: Report file successfully saved on disk; database record initialized.
* **`PROCESSING`**: Report pipeline currently executing.
* **`OCR_COMPLETE`**: Document parsed; digital page text extracted.
* **`EXTRACTION_COMPLETE`**: Diagnostic parameters, medications, and allergies structured.
* **`RISK_COMPLETE`**: Severity scoring and recommendations completed.
* **`SUMMARY_COMPLETE`**: Executive longitudinal summaries generated.
* **`SYNC_COMPLETE`**: MongoDB patient memory logs and Qdrant points updated.
* **`READY`**: Post-execution validator confirmed total synchronization alignment.
* **`FAILED`**: Execution halted due to terminal stage failures.
* **`PARTIAL_SUCCESS`**: Pipeline finished, but indexing validation found minor structural warnings.

---

## 3. Retry Strategy & Failure Recovery

The orchestrator guarantees high reliability using two retry strategies:

1. **Stage-level Retry with Exponential Backoff**:
   - Each individual stage (OCR, Extraction, etc.) retries up to 3 times internally.
   - Retries apply exponential backoff (e.g. 1s -> 2s -> 4s) to wait for transient external failures.
2. **Partial Recovery & Resumption**:
   - If a stage fails Terminally (depleting its retries), the pipeline is marked as `FAILED`.
   - Admin/Developer can invoke `POST /reports/{report_id}/pipeline/retry`.
   - The orchestrator analyzes the database document status keys.
   - Successful stages are skipped (e.g. if `ocr_status == "completed"`, OCR is bypassed).
   - Execution resumes directly at the failed stage, saving LLM tokens and API roundtrips.

---

## 4. Production Telemetry

The `PipelineTelemetry` collects real-time stats stored in MongoDB collections (`pipeline_telemetry` and `pipeline_retries`):
- Stage execution times (OCR, extraction, risk, summary, sync).
- Success and failure rates.
- Processing queue depths.
- Common error messages logged by the orchestrator.
- Health ratings (healthy vs degraded based on error frequency).
