"""
Nura - Medical Report and Health Insight Repositories Tests
Unit tests for ReportRepository and HealthInsightRepository using mocked MongoDB collections.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from bson import ObjectId

from app.models.report import (
    ReportCreate,
    ReportUpdate,
    ReportInDB,
    ReportType,
    ProcessingStatus,
    RiskLevel,
    HealthInsightCreate,
    HealthInsightUpdate,
    HealthInsightInDB,
    InsightType,
    Severity,
)
from app.repositories.report_repository import ReportRepository
from app.repositories.health_insight_repository import HealthInsightRepository


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_report_doc(
    report_id: str = "507f1f77bcf86cd799439080",
    patient_id: str = "507f1f77bcf86cd799439001",
    uploaded_by: str = "507f1f77bcf86cd799439001",
) -> dict:
    now = utc_now()
    return {
        "_id": ObjectId(report_id),
        "patient_id": patient_id,
        "uploaded_by": uploaded_by,
        "report_type": "blood_test",
        "file_url": "https://example.com/blood_test.pdf",
        "raw_text": "Hemoglobin: 14.5 g/dL",
        "structured_data": {"hemoglobin": 14.5},
        "entities": [],
        "ai_summary": "Normal.",
        "risk_level": "low",
        "processing_status": "completed",
        "created_at": now,
        "updated_at": now,
    }


def make_insight_doc(
    insight_id: str = "507f1f77bcf86cd799439090",
    patient_id: str = "507f1f77bcf86cd799439001",
    source_report_id: str = "507f1f77bcf86cd799439080",
) -> dict:
    now = utc_now()
    return {
        "_id": ObjectId(insight_id),
        "patient_id": patient_id,
        "insight_type": "trend",
        "title": "Cholesterol Decreasing",
        "description": "Down 15mg/dL over past 3 months.",
        "severity": "low",
        "source_report_id": source_report_id,
        "created_at": now,
    }


def make_mock_collection(find_one_return=None, find_return=None, update_result=None):
    collection = MagicMock()
    collection.find_one = AsyncMock(return_value=find_one_return)

    insert_result = MagicMock()
    insert_result.inserted_id = ObjectId("507f1f77bcf86cd799439080")
    collection.insert_one = AsyncMock(return_value=insert_result)

    upd_result = MagicMock()
    upd_result.modified_count = 1 if update_result is None else update_result
    collection.update_one = AsyncMock(return_value=upd_result)

    del_result = MagicMock()
    del_result.deleted_count = 1
    collection.delete_one = AsyncMock(return_value=del_result)

    cursor = MagicMock()
    cursor.skip = MagicMock(return_value=cursor)
    cursor.limit = MagicMock(return_value=cursor)
    cursor.to_list = AsyncMock(return_value=find_return or [])
    collection.find = MagicMock(return_value=cursor)

    return collection


# ---------------------------------------------------------------------------
# Test Classes
# ---------------------------------------------------------------------------

class TestReportRepository:
    @pytest.mark.asyncio
    async def test_create_report(self):
        doc = make_report_doc()
        collection = make_mock_collection(find_one_return=doc)
        repo = ReportRepository(collection)

        report_create = ReportCreate(
            patient_id="507f1f77bcf86cd799439001",
            uploaded_by="507f1f77bcf86cd799439001",
            report_type=ReportType.BLOOD_TEST,
            file_url="https://example.com/blood_test.pdf",
        )
        result = await repo.create(report_create)
        assert isinstance(result, ReportInDB)
        assert result.patient_id == "507f1f77bcf86cd799439001"
        assert result.processing_status == ProcessingStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_get_report(self):
        doc = make_report_doc()
        collection = make_mock_collection(find_one_return=doc)
        repo = ReportRepository(collection)

        result = await repo.get_by_id("507f1f77bcf86cd799439080")
        assert result is not None
        assert result.id == "507f1f77bcf86cd799439080"

    @pytest.mark.asyncio
    async def test_get_by_patient_id(self):
        docs = [make_report_doc()]
        collection = make_mock_collection(find_return=docs)
        repo = ReportRepository(collection)

        results = await repo.get_by_patient_id("507f1f77bcf86cd799439001")
        assert len(results) == 1
        assert results[0].patient_id == "507f1f77bcf86cd799439001"

    @pytest.mark.asyncio
    async def test_update_report(self):
        updated_doc = make_report_doc()
        updated_doc["processing_status"] = "processing"
        collection = make_mock_collection(find_one_return=updated_doc)
        repo = ReportRepository(collection)

        update = ReportUpdate(processing_status=ProcessingStatus.PROCESSING)
        result = await repo.update("507f1f77bcf86cd799439080", update)
        assert result is not None
        assert result.processing_status == ProcessingStatus.PROCESSING

    @pytest.mark.asyncio
    async def test_delete_report(self):
        collection = make_mock_collection()
        repo = ReportRepository(collection)
        result = await repo.delete("507f1f77bcf86cd799439080")
        assert result is True

    @pytest.mark.asyncio
    async def test_list_reports(self):
        docs = [make_report_doc()]
        collection = make_mock_collection(find_return=docs)
        repo = ReportRepository(collection)

        results = await repo.list()
        assert len(results) == 1


class TestHealthInsightRepository:
    @pytest.mark.asyncio
    async def test_create_insight(self):
        doc = make_insight_doc()
        collection = make_mock_collection(find_one_return=doc)
        collection.insert_one.return_value.inserted_id = ObjectId("507f1f77bcf86cd799439090")
        repo = HealthInsightRepository(collection)

        insight_create = HealthInsightCreate(
            patient_id="507f1f77bcf86cd799439001",
            insight_type=InsightType.TREND,
            title="Cholesterol Decreasing",
            description="Down 15mg/dL over past 3 months.",
            severity=Severity.LOW,
            source_report_id="507f1f77bcf86cd799439080",
        )
        result = await repo.create(insight_create)
        assert isinstance(result, HealthInsightInDB)
        assert result.id == "507f1f77bcf86cd799439090"

    @pytest.mark.asyncio
    async def test_get_by_patient_id(self):
        docs = [make_insight_doc()]
        collection = make_mock_collection(find_return=docs)
        repo = HealthInsightRepository(collection)

        results = await repo.get_by_patient_id("507f1f77bcf86cd799439001")
        assert len(results) == 1
        assert results[0].patient_id == "507f1f77bcf86cd799439001"
