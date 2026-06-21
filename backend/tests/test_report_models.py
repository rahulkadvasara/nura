"""
Nura - Medical Report and Health Insight Models Tests
Tests for reports and health_insights Pydantic models
"""

import pytest
from datetime import datetime, timezone
from bson import ObjectId

from app.models.report import (
    ReportType,
    ProcessingStatus,
    RiskLevel,
    InsightType,
    Severity,
    ReportCreate,
    ReportUpdate,
    ReportInDB,
    HealthInsightCreate,
    HealthInsightUpdate,
    HealthInsightInDB,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TestReportEnums:
    def test_report_type_values(self):
        assert ReportType.BLOOD_TEST == "blood_test"
        assert ReportType.PRESCRIPTION == "prescription"
        assert ReportType.IMAGING == "imaging"
        assert ReportType.DISCHARGE_SUMMARY == "discharge_summary"
        assert ReportType.OTHER == "other"

    def test_processing_status_values(self):
        assert ProcessingStatus.UPLOADED == "uploaded"
        assert ProcessingStatus.PROCESSING == "processing"
        assert ProcessingStatus.COMPLETED == "completed"
        assert ProcessingStatus.FAILED == "failed"

    def test_risk_level_values(self):
        assert RiskLevel.LOW == "low"
        assert RiskLevel.MEDIUM == "medium"
        assert RiskLevel.HIGH == "high"

    def test_insight_type_values(self):
        assert InsightType.TREND == "trend"
        assert InsightType.ANOMALY == "anomaly"
        assert InsightType.RECOMMENDATION == "recommendation"
        assert InsightType.REMINDER == "reminder"

    def test_severity_values(self):
        assert Severity.LOW == "low"
        assert Severity.MEDIUM == "medium"
        assert Severity.HIGH == "high"


class TestReportModel:
    def test_create_report(self):
        report = ReportCreate(
            patient_id="507f1f77bcf86cd799439001",
            uploaded_by="507f1f77bcf86cd799439001",
            report_type=ReportType.BLOOD_TEST,
            file_url="https://example.com/blood_test.pdf",
            raw_text="Hemoglobin: 14.5 g/dL",
            structured_data={"hemoglobin": 14.5},
            entities=[{"text": "Hemoglobin", "label": "BIOMARKER"}],
            ai_summary="Normal hemoglobin levels.",
            risk_level=RiskLevel.LOW,
            processing_status=ProcessingStatus.COMPLETED
        )
        assert report.patient_id == "507f1f77bcf86cd799439001"
        assert report.report_type == ReportType.BLOOD_TEST
        assert report.raw_text == "Hemoglobin: 14.5 g/dL"
        assert report.structured_data == {"hemoglobin": 14.5}
        assert len(report.entities) == 1
        assert report.ai_summary == "Normal hemoglobin levels."
        assert report.risk_level == RiskLevel.LOW
        assert report.processing_status == ProcessingStatus.COMPLETED

    def test_report_default_values(self):
        report = ReportCreate(
            patient_id="patient_1",
            uploaded_by="patient_1",
            file_url="https://example.com/report.pdf",
        )
        assert report.report_type == ReportType.OTHER
        assert report.raw_text is None
        assert report.structured_data is None
        assert report.entities is None
        assert report.ai_summary is None
        assert report.risk_level == RiskLevel.LOW
        assert report.processing_status == ProcessingStatus.UPLOADED

    def test_report_update_partial(self):
        update = ReportUpdate(processing_status=ProcessingStatus.PROCESSING, risk_level=RiskLevel.MEDIUM)
        assert update.processing_status == ProcessingStatus.PROCESSING
        assert update.risk_level == RiskLevel.MEDIUM
        assert update.file_url is None

    def test_report_in_db_from_mongo(self):
        now = utc_now()
        raw = {
            "_id": ObjectId("507f1f77bcf86cd799439080"),
            "patient_id": ObjectId("507f1f77bcf86cd799439001"),
            "uploaded_by": ObjectId("507f1f77bcf86cd799439002"),
            "report_type": "blood_test",
            "file_url": "https://example.com/report.pdf",
            "raw_text": None,
            "structured_data": None,
            "entities": None,
            "ai_summary": None,
            "risk_level": "low",
            "processing_status": "uploaded",
            "created_at": now,
            "updated_at": now,
        }
        report = ReportInDB.from_mongo(raw)
        assert report.id == "507f1f77bcf86cd799439080"
        assert report.patient_id == "507f1f77bcf86cd799439001"
        assert report.uploaded_by == "507f1f77bcf86cd799439002"
        assert report.created_at == now


class TestHealthInsightModel:
    def test_create_health_insight(self):
        insight = HealthInsightCreate(
            patient_id="507f1f77bcf86cd799439001",
            insight_type=InsightType.RECOMMENDATION,
            title="Increase Iron Intake",
            description="Your recent blood test shows slightly low iron. Consider eating more spinach.",
            severity=Severity.MEDIUM,
            source_report_id="507f1f77bcf86cd799439080"
        )
        assert insight.patient_id == "507f1f77bcf86cd799439001"
        assert insight.insight_type == InsightType.RECOMMENDATION
        assert insight.title == "Increase Iron Intake"
        assert insight.severity == Severity.MEDIUM
        assert insight.source_report_id == "507f1f77bcf86cd799439080"

    def test_health_insight_default_values(self):
        insight = HealthInsightCreate(
            patient_id="patient_1",
            insight_type=InsightType.ANOMALY,
            title="High BP Reading",
            description="Systolic BP of 145 mmHg.",
        )
        assert insight.severity == Severity.LOW
        assert insight.source_report_id is None

    def test_health_insight_in_db_from_mongo(self):
        now = utc_now()
        raw = {
            "_id": ObjectId("507f1f77bcf86cd799439090"),
            "patient_id": ObjectId("507f1f77bcf86cd799439001"),
            "insight_type": "trend",
            "title": "Cholesterol Decreasing",
            "description": "Down 15mg/dL over past 3 months.",
            "severity": "low",
            "source_report_id": ObjectId("507f1f77bcf86cd799439080"),
            "created_at": now,
        }
        insight = HealthInsightInDB.from_mongo(raw)
        assert insight.id == "507f1f77bcf86cd799439090"
        assert insight.patient_id == "507f1f77bcf86cd799439001"
        assert insight.source_report_id == "507f1f77bcf86cd799439080"
        assert insight.created_at == now
