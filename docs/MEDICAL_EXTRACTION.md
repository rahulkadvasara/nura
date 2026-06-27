# Medical Information Extraction Pipeline

This document details the production-ready medical information extraction architecture in the Nura Healthcare Platform.

## Architecture & Flow

```text
Raw / Normalized OCR Text (MongoDB)
            │
            ▼
DocumentClassifier (Blood Test, CBC, Prescription, Radiology, etc.)
            │
            ▼
MedicalEntityExtractor (Patient info, Hospital details, Entities array)
            │
            ▼
LaboratoryParser / MedicationParser (Blood values, drugs lists)
            │
            ▼
MedicalNormalizer (Standardize dates, units; merge duplicate items)
            │
            ▼
ExtractionValidator (Check ranges, empty sections; write warning logs)
            │
            ▼
MongoDB (Update Report document fields; trigger extraction telemetry)
```

## Core Components

### 1. Document Classifier
Classifies reports into structured clinical categories:
- `Blood Test`
- `CBC` (Complete Blood Count)
- `Liver Function`
- `Kidney Function`
- `Lipid Profile`
- `Diabetes`
- `Thyroid`
- `Urine`
- `Prescription`
- `Radiology`
- `Discharge Summary`
- `Consultation Note`
- `Other`

Features a regex keyword fallback in case LLM requests fail or time out (testing environments).

### 2. Medical Entity Extractor
Extracts:
- **Patient Information**: `patient_name`, `age`, `gender`, `date_of_birth`, `patient_id`.
- **Hospital Information**: `hospital`, `laboratory`, `doctor`, `department`, `report_date`.
- **Entities List**: Medical terms classified into `diagnoses`, `symptoms`, `diseases`, `allergies`, `procedures`, `medications`, `surgeries`, `vaccinations`, `family_history`, tracking confidence, page number, and document location.

### 3. Parsers & Normalizers
- **Laboratory Result Parser**: Standardizes test metrics, converting parameter value strings to floats, standardizing units (e.g. `g/dl` -> `g/dL`), and normalizing alert status values (`NORMAL`, `HIGH`, `LOW`, `ABNORMAL`).
- **Medication Parser**: Standardizes drug items, administration frequencies, treatment durations, and routes.
- **De-duplication**: Filters out duplicate test metrics by parameter name, merges duplicate medication items, and consolidates case-insensitive duplicate diagnoses or allergy strings.

### 4. Layout Validation
- Audits numerical test parameters.
- Validates date layouts against standard ISO `YYYY-MM-DD` templates.
- Highlights clinical empty layout categories, generating warning list logs saved under `extraction_warnings`.

---

## MongoDB Model Schema Additions

The `Report` model contains the following clinical extraction fields:
```python
document_type: Optional[str]          # Classified category
structured_data: Optional[Dict]       # Patient, Hospital details and Metadata
entities: Optional[List[Dict]]        # Clinical variables mapped
laboratory_results: Optional[List]    # Tabular lab results
medications: Optional[List]           # Prescribed drugs
diagnoses: Optional[List[str]]        # Merged diagnoses strings
allergies: Optional[List[str]]        # Merged allergies strings
extraction_status: Optional[str]      # pending, processing, completed, failed
extraction_confidence: Optional[float]
extraction_version: Optional[str]
extraction_warnings: Optional[List[str]]
```

---

## API Endpoints

- `POST /api/v1/reports/{report_id}/extract`: Manually trigger medical information extraction.
- `GET /api/v1/reports/{report_id}/structured`: Fetch structured results JSON.
- `GET /api/v1/reports/{report_id}/entities`: Get medical entities array.
- `GET /api/v1/reports/telemetry/extraction`: Get pipeline extraction telemetry stats.
