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
from app.core.dependencies import get_current_user, get_report_service, get_report_understanding_service
from app.models.user import UserInDB, UserRole
from app.models.report import ReportInDB, ProcessingStatus, ReportType, RiskLevel

# Construct test FastAPI app instance
app = FastAPI()
app.include_router(router)


@pytest.mark.asyncio
async def test_summarize_report_endpoint():
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
        overall_risk="LOW",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    mock_report_service = MagicMock()
    mock_report_service.get_report_by_id = AsyncMock(return_value=mock_report)

    mock_understanding_service = MagicMock()
    mock_understanding_service.generate_report_summary = AsyncMock(return_value=mock_report)

    # Inject overrides
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_report_service] = lambda: mock_report_service
    app.dependency_overrides[get_report_understanding_service] = lambda: mock_understanding_service

    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/report_123/summarize")
        assert res.status_code == 200
        assert res.json()["success"] is True
        assert "triggered" in res.json()["message"].lower()

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_report_summary_endpoint():
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
        overall_risk="LOW",
        ai_summary="Exec Summary overview text.",
        patient_summary="Simple friendly descriptions.",
        doctor_summary="Clinical interpretation details.",
        summary_confidence=0.92,
        summary_version="1.0.0",
        summary_generated_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    mock_report_service = MagicMock()
    mock_report_service.get_report_by_id = AsyncMock(return_value=mock_report)

    # Inject overrides
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_report_service] = lambda: mock_report_service

    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/report_123/summary")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["ai_summary"] == "Exec Summary overview text."
        assert data["patient_summary"] == "Simple friendly descriptions."
        assert data["summary_confidence"] == 0.92

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_ai_telemetry_forbidden():
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

    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/ai/statistics")
        # Should raise 403 forbidden for patient role
        assert res.status_code == 403

    app.dependency_overrides.clear()
