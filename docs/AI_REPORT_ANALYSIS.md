# Clinical AI Report Analysis & Understanding

This document outlines the pipeline, prompts structure, agent coordination, and telemetry tracking for Phase 11 - Sprint 4: AI Report Understanding & Clinical Summarization.

## 1. Architectural Processing Pipeline

```text
Normalized OCR Text
        │
        ▼
Document Classification
        │
        ▼
Medical Entity Extraction & Lab Parsing (Sprint 2)
        │
        ▼
Clinical Risk Analysis Rules & Scoring (Sprint 3)
        │
        ▼
Patient Context Builder & Qdrant History Retrieval (via ReportAnalysisAgent)
        │
        ▼
Unified AI Summary Prompts (Sprint 4)
        │
        ▼
Groq LLM Generation (Structured JSON)
        │
        ▼
MongoDB Storage & Telemetry logging
```

---

## 2. Agent Reuse Strategy

To avoid code duplication and exploit context retrieval, the pipeline reuse strategy works as follows:
1. **ReportAnalysisAgent**: Initiates retrieval from Qdrant vector store and MongoDB context indices, fetching patient history logs and previous summaries.
2. **AIService**: Central client coordinating Groq execution, latency logging, cost calculation, and failure metrics registry.
3. **PromptLoader**: Extracted and sub-classed inside `ReportPromptLoader` to read markdown template prompts from `backend/app/prompts/report/` folder.

---

## 3. Prompts Flow

The final summarization prompt uses five separate templates:
1. **`report_summary_system.md`**: Tells the assistant to return structured JSON.
2. **`patient_summary.md`**: Simple patient-friendly observations template.
3. **`doctor_summary.md`**: Clinical diagnostic interpretations template.
4. **`clinical_insights.md`**: Trend warnings and preventative recommendations template.
5. **`followup_questions.md`**: Key questions a patient can ask their doctor.

---

## 4. Confidence & Fallbacks

- **Confidence Scoring**: Each generation outputs a confidence factor (e.g. `0.95`).
- **Resilient Fallback**: If the LLM is offline or times out, the local `SummaryService` and `InsightService` construct logical fallbacks from rule findings and parsed laboratory metrics.
