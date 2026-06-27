# Clinical Risk Assessment System Documentation

This document describes the design, implementation, and extensibility of the structured Clinical Risk Assessment and recommendation engine of the Nura Healthcare Platform.

## Architecture Diagram

```text
  Structured Extraction (MongoDB)
                │
                ▼
      ┌──────────────────┐
      │LaboratoryAnalyzer│ (Evaluates parameters bounds: low, normal, high, critical)
      └─────────┬────────┘
                ▼
      ┌──────────────────┐
      │  ClinicalRules   │ (Diabetes, Hypertension, Kidney, Liver, Thyroid, Lipids, Infection)
      └─────────┬────────┘
                ▼
      ┌──────────────────┐
      │    RiskEngine    │ (AI justifications generator, risk score calculations)
      └─────────┬────────┘
                ▼
      ┌──────────────────┐
      │  Recommendation  │ (Repeat test, Consult physician, Emergency care, Specialist referral)
      │      Engine      │
      └─────────┬────────┘
                ▼
    Clinical Risk Assessment (Saved to MongoDB Report)
```

---

## 1. Laboratory Evaluation (`LaboratoryAnalyzer`)
The `LaboratoryAnalyzer` parses numeric reference bounds and evaluates individual results values against them:
* **Statuses Mapped**: `NORMAL`, `LOW`, `HIGH`, `CRITICAL_LOW`, `CRITICAL_HIGH`
* **Critical Alarm Limits**:
  * Hemoglobin: Low <= 7.0 g/dL, High >= 20.0 g/dL
  * Glucose: Low <= 50 mg/dL, High >= 300 mg/dL
  * Creatinine: High >= 3.0 mg/dL
  * WBC: Low <= 2.0 k/uL, High >= 30.0 k/uL
  * Potassium: Low <= 3.0 mEq/L, High >= 6.2 mEq/L
* **Fallback Ranges**: Mapped automatically for common tests if the report's reference ranges are missing or parsing fails.

---

## 2. Extensible Rule Engine (`ClinicalRules`)
Clinical rules are modular classes implementing `BaseRule`. This allows you to add or modify rules without altering the core pipeline.
Supported rules:
* **Diabetes**: Triggered by HbA1c >= 5.7% (Prediabetes) or >= 6.5% (Diabetes), and Fasting Glucose >= 126 mg/dL.
* **Kidney Disease**: Triggered by eGFR < 60 mL/min/1.73m² or Serum Creatinine > 1.2 mg/dL.
* **Liver Abnormalities**: Triggered by elevated AST/ALT > 50 U/L or Bilirubin > 1.2 mg/dL.
* **Thyroid Abnormalities**: Triggered by TSH > 4.5 uIU/mL (Hypo) or < 0.4 uIU/mL (Hyper).
* **Lipid Abnormalities**: Triggered by Total Cholesterol > 200 mg/dL or LDL > 130 mg/dL.
* **Anemia Indicators**: Triggered by Hemoglobin < 12.0 g/dL.
* **Infection Indicators**: Triggered by WBC > 11.0 k/uL (Leukocytosis) or < 4.0 k/uL (Leukopenia).

---

## 3. Risk Engine Scoring (`RiskEngine`)
Scores are computed between `0.0` and `100.0` based on rule triggers and critical alarms:
* **Critical findings weight**: 35.0 points
* **High findings weight**: 25.0 points
* **Medium findings weight**: 15.0 points
* **Low findings weight**: 7.0 points

Overall Severity classifications mapping:
* **CRITICAL**: Any CRITICAL flag OR Score >= 60.0
* **HIGH**: Any HIGH flag OR Score >= 40.0
* **MEDIUM**: Any MEDIUM flag OR Score >= 20.0
* **LOW**: Any LOW flag OR Score > 0.0
* **NORMAL**: All other cases

---

## 4. Structured Recommendations (`RecommendationEngine`)
Structured recommendations are generated dynamically based on findings:
* **Emergency attention**: Triggered by critical lab values.
* **Consult physician**: Triggered by High/Critical findings.
* **Specialist referral**: Mapped to specific organ or chronic rules (e.g., Endocrinologist for Diabetes, Nephrologist for Kidney).
* **Lifestyle modification**: Diet and exercise suggestions for lipids or diabetes.
* **Medication review**: Suggested when kidney functions are impaired.
* **Repeat laboratory test**: Suggested standard follow-up timeline (2-4 weeks).

> [!WARNING]
> All recommendation items are informational. They do not constitute diagnostic medical advice and are paired with a standard legal disclaimer.

---

## 5. Extensibility Guidelines
To add a new rule:
1. Create a class inheriting from `BaseRule` in `clinical_rules.py`.
2. Implement the `evaluate(self, labs: List[dict], medications: List[dict] = None) -> List[dict]` method.
3. Register the new rule instance in the `ClinicalRules` list inside `__init__`.
