import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

import pytest
import httpx
from httpx import ASGITransport
from fastapi import FastAPI
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from app.api.v1.reports import router
from app.core.dependencies import (
    get_current_user,
    get_report_service,
    get_pipeline_service,
    get_pipeline_telemetry
)
from app.models.user import UserInDB, UserRole
from app.models.report import ReportInDB, ProcessingStatus, ReportType, RiskLevel

# Construct test FastAPI app instance
app = FastAPI()
app.include_router(router)


@pytest.mark.asyncio
async def test_get_pipeline_statistics_endpoint():
    mock_admin = UserInDB(
        id="admin_123",
        email="admin@nura.com",
        password_hash="...",
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    mock_telemetry = MagicMock()
    mock_telemetry.get_statistics = AsyncMock(return_value={
        "throughput": 10,
        "averages": {"avg_ocr_ms": 150.0},
        "health": "healthy"
    })

    app.dependency_overrides[get_current_user] = lambda: mock_admin
    app.dependency_overrides[get_pipeline_telemetry] = lambda: mock_telemetry

    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/pipeline/statistics")
        assert res.status_code == 200
        assert res.json()["success"] is True
        assert res.json()["data"]["health"] == "healthy"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_report_pipeline_status_endpoint():
    mock_user = UserInDB(
        id="user_abc",
        email="test@nura.com",
        password_hash="...",
        full_name="Test Patient",
        role=UserRole.PATIENT,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    mock_report = ReportInDB(
        id="report_123",
        patient_id="user_abc",
        uploaded_by="user_abc",
        report_type=ReportType.BLOOD_TEST,
        file_url="http://storage/report.pdf",
        processing_status=ProcessingStatus.COMPLETED,
        risk_level=RiskLevel.LOW,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    mock_report_service = MagicMock()
    mock_report_service.get_report_by_id = AsyncMock(return_value=mock_report)

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_report_service] = lambda: mock_report_service

    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/report_123/pipeline")
        assert res.status_code == 200
        assert res.json()["success"] is True
        assert res.json()["data"]["report_id"] == "report_123"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_retry_pipeline_endpoint():
    mock_user = UserInDB(
        id="user_abc",
        email="test@nura.com",
        password_hash="...",
        full_name="Test Patient",
        role=UserRole.PATIENT,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    mock_report = ReportInDB(
        id="report_123",
        patient_id="user_abc",
        uploaded_by="user_abc",
        report_type=ReportType.BLOOD_TEST,
        file_url="http://storage/report.pdf",
        processing_status=ProcessingStatus.COMPLETED,
        risk_level=RiskLevel.LOW,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    mock_report_service = MagicMock()
    mock_report_service.get_report_by_id = AsyncMock(return_value=mock_report)

    mock_pipeline_service = MagicMock()
    mock_pipeline_service.execute_pipeline = AsyncMock(return_value={"success": True})

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_report_service] = lambda: mock_report_service
    app.dependency_overrides[get_pipeline_service] = lambda: mock_pipeline_service

    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/report_123/pipeline/retry")
        assert res.status_code == 200
        assert res.json()["success"] is True

    app.dependency_overrides.clear()
