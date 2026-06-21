"""
Nura - Medical Report and Health Insight Services Tests
Unit tests for ReportService and HealthInsightService using mocked repositories.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from bson import ObjectId

from app.models.report import (
    ReportInDB,
    ReportType,
    ProcessingStatus,
    RiskLevel,
    HealthInsightInDB,
    InsightType,
    Severity,
)
from app.models.user import UserInDB, UserRole, AuthProvider
from app.schemas.report import (
    ReportCreateSchema,
    ReportUpdateSchema,
    HealthInsightCreateSchema,
    HealthInsightUpdateSchema,
)
from app.services.report_service import ReportService
from app.services.health_insight_service import HealthInsightService


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_user():
    return UserInDB(
        id="507f1f77bcf86cd799439001",
        role=UserRole.PATIENT,
        email="patient@example.com",
        password_hash="hashed_pw",
        full_name="Patient Name",
        phone="1234567890",
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True,
        created_at=utc_now(),
        updated_at=utc_now(),
    )


@pytest.fixture
def sample_report():
    return ReportInDB(
        id="507f1f77bcf86cd799439080",
        patient_id="507f1f77bcf86cd799439001",
        uploaded_by="507f1f77bcf86cd799439001",
        report_type=ReportType.BLOOD_TEST,
        file_url="https://example.com/blood_test.pdf",
        raw_text=None,
        structured_data=None,
        entities=None,
        ai_summary=None,
        risk_level=RiskLevel.LOW,
        processing_status=ProcessingStatus.UPLOADED,
        created_at=utc_now(),
        updated_at=utc_now(),
    )


@pytest.fixture
def sample_insight():
    return HealthInsightInDB(
        id="507f1f77bcf86cd799439090",
        patient_id="507f1f77bcf86cd799439001",
        insight_type=InsightType.RECOMMENDATION,
        title="Increase Iron Intake",
        description="Eat more spinach.",
        severity=Severity.LOW,
        source_report_id="507f1f77bcf86cd799439080",
        created_at=utc_now(),
    )


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

class TestReportService:
    @pytest.mark.asyncio
    async def test_create_report_success(self, sample_user, sample_report):
        rep_repo = AsyncMock()
        rep_repo.collection = MagicMock()
        rep_repo.collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439080"))
        )
        rep_repo.collection.find_one = AsyncMock(return_value={
            "_id": ObjectId("507f1f77bcf86cd799439080"),
            "patient_id": sample_user.id,
            "uploaded_by": sample_user.id,
            "report_type": "blood_test",
            "file_url": "https://example.com/blood_test.pdf",
            "raw_text": None,
            "structured_data": None,
            "entities": None,
            "ai_summary": None,
            "risk_level": "low",
            "processing_status": "uploaded",
            "created_at": utc_now(),
            "updated_at": utc_now(),
        })

        user_repo = AsyncMock()
        user_repo.get = AsyncMock(return_value=sample_user)

        service = ReportService(rep_repo, user_repo)
        schema = ReportCreateSchema(
            patient_id=sample_user.id,
            uploaded_by=sample_user.id,
            report_type=ReportType.BLOOD_TEST,
            file_url="https://example.com/blood_test.pdf",
        )

        result = await service.create_report(schema)
        assert isinstance(result, ReportInDB)
        assert result.id == "507f1f77bcf86cd799439080"
        assert user_repo.get.call_count == 2  # once for patient, once for uploader

    @pytest.mark.asyncio
    async def test_create_report_patient_not_found(self, sample_user):
        rep_repo = AsyncMock()
        user_repo = AsyncMock()
        # Mock get returning None for first call (patient)
        user_repo.get = AsyncMock(return_value=None)

        service = ReportService(rep_repo, user_repo)
        schema = ReportCreateSchema(
            patient_id="invalid_patient",
            uploaded_by=sample_user.id,
            report_type=ReportType.BLOOD_TEST,
            file_url="https://example.com/blood_test.pdf",
        )

        with pytest.raises(ValueError, match="Patient.*does not exist"):
            await service.create_report(schema)

    @pytest.mark.asyncio
    async def test_create_report_uploader_not_found(self, sample_user):
        rep_repo = AsyncMock()
        user_repo = AsyncMock()
        # Mock get returning patient user first, then None for uploader
        user_repo.get = AsyncMock(side_effect=[sample_user, None])

        service = ReportService(rep_repo, user_repo)
        schema = ReportCreateSchema(
            patient_id=sample_user.id,
            uploaded_by="invalid_uploader",
            report_type=ReportType.BLOOD_TEST,
            file_url="https://example.com/blood_test.pdf",
        )

        with pytest.raises(ValueError, match="Uploading user.*does not exist"):
            await service.create_report(schema)


class TestHealthInsightService:
    @pytest.mark.asyncio
    async def test_create_insight_success(self, sample_user, sample_report, sample_insight):
        ins_repo = AsyncMock()
        ins_repo.collection = MagicMock()
        ins_repo.collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439090"))
        )
        ins_repo.collection.find_one = AsyncMock(return_value={
            "_id": ObjectId("507f1f77bcf86cd799439090"),
            "patient_id": sample_user.id,
            "insight_type": "recommendation",
            "title": "Increase Iron Intake",
            "description": "Eat more spinach.",
            "severity": "low",
            "source_report_id": sample_report.id,
            "created_at": utc_now(),
        })

        user_repo = AsyncMock()
        user_repo.get = AsyncMock(return_value=sample_user)

        rep_repo = AsyncMock()
        rep_repo.get = AsyncMock(return_value=sample_report)

        service = HealthInsightService(ins_repo, user_repo, rep_repo)
        schema = HealthInsightCreateSchema(
            patient_id=sample_user.id,
            insight_type=InsightType.RECOMMENDATION,
            title="Increase Iron Intake",
            description="Eat more spinach.",
            severity=Severity.LOW,
            source_report_id=sample_report.id,
        )

        result = await service.create_insight(schema)
        assert isinstance(result, HealthInsightInDB)
        assert result.id == "507f1f77bcf86cd799439090"
        user_repo.get.assert_called_once_with(sample_user.id)
        rep_repo.get.assert_called_once_with(sample_report.id)

    @pytest.mark.asyncio
    async def test_create_insight_patient_not_found(self, sample_report):
        ins_repo = AsyncMock()
        user_repo = AsyncMock()
        user_repo.get = AsyncMock(return_value=None)
        rep_repo = AsyncMock()

        service = HealthInsightService(ins_repo, user_repo, rep_repo)
        schema = HealthInsightCreateSchema(
            patient_id="invalid_patient",
            insight_type=InsightType.RECOMMENDATION,
            title="A",
            description="B",
            source_report_id=sample_report.id,
        )

        with pytest.raises(ValueError, match="Patient.*does not exist"):
            await service.create_insight(schema)

    @pytest.mark.asyncio
    async def test_create_insight_source_report_not_found(self, sample_user):
        ins_repo = AsyncMock()
        user_repo = AsyncMock()
        user_repo.get = AsyncMock(return_value=sample_user)
        rep_repo = AsyncMock()
        rep_repo.get = AsyncMock(return_value=None)

        service = HealthInsightService(ins_repo, user_repo, rep_repo)
        schema = HealthInsightCreateSchema(
            patient_id=sample_user.id,
            insight_type=InsightType.RECOMMENDATION,
            title="A",
            description="B",
            source_report_id="invalid_report",
        )

        with pytest.raises(ValueError, match="Source report.*does not exist"):
            await service.create_insight(schema)
