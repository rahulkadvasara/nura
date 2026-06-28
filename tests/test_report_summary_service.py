import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

import pytest
from app.services.report_ai.summary_service import SummaryService
from app.services.report_ai.insight_service import InsightService


def test_fallback_summaries_normal():
    service = SummaryService()
    res = service.generate_fallback_summaries(
        demographics={"patient_name": "Alice", "age": 28, "gender": "Female"},
        labs=[],
        risk_findings=[]
    )
    assert "Alice" in res["ai_summary"]
    assert "normal ranges" in res["patient_summary"]
    assert "stability" in res["doctor_summary"]
    assert res["confidence"] == 0.65


def test_fallback_summaries_abnormal():
    service = SummaryService()
    res = service.generate_fallback_summaries(
        demographics={"patient_name": "Bob", "age": 45, "gender": "Male"},
        labs=[{"test_name": "HbA1c", "value": "7.5", "unit": "%", "is_abnormal": True}],
        risk_findings=[{"finding_name": "Diabetes Indicator (HbA1c)", "message": "HbA1c is high"}]
    )
    assert "Bob" in res["ai_summary"]
    assert "out-of-range" in res["patient_summary"]
    assert "HbA1c" in res["ai_summary"]


def test_fallback_insights():
    service = InsightService()
    res = service.generate_fallback_insights(
        labs=[{"test_name": "HbA1c", "value": "7.5", "unit": "%", "is_abnormal": True}],
        risk_findings=[{"finding_name": "Diabetes Indicator (HbA1c)", "severity": "HIGH", "flag": "DIABETES_MARKER", "message": "HbA1c is high"}],
        recommendations=[]
    )
    assert len(res["key_findings"]) > 0
    assert len(res["clinical_insights"]) > 0
    assert len(res["followup_questions"]) > 0
    assert any("HbA1c" in f for f in res["key_findings"])
    assert any("Glucose metabolism" in c for c in res["clinical_insights"])
