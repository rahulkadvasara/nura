import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

import pytest
import httpx
from httpx import ASGITransport
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, status
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from app.api.v1.reports import router
from app.core.dependencies import get_current_user, get_report_service, get_risk_analysis_service
from app.models.user import UserInDB, UserRole
from app.models.report import ReportInDB, ProcessingStatus, ReportType, RiskLevel

# Construct test FastAPI app instance
app = FastAPI()
app.include_router(router)


@pytest.mark.asyncio
async def test_risk_analysis_trigger_authorized():
    mock_user = UserInDB(
        id="user_123",
        email="test@nura.com",
        password_hash="...",
        full_name="Test Patient",
        role=UserRole.PATIENT,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    mock_report = ReportInDB(
        id="report_abc",
        patient_id="user_123",
        uploaded_by="user_123",
        report_type=ReportType.BLOOD_TEST,
        file_url="http://storage/report.pdf",
        processing_status=ProcessingStatus.COMPLETED,
        risk_level=RiskLevel.LOW,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    mock_report_service = MagicMock()
    mock_report_service.get_report_by_id = AsyncMock(return_value=mock_report)

    mock_risk_service = MagicMock()
    mock_risk_service.analyze_report_risks = AsyncMock(return_value=mock_report)

    # Inject overrides
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_report_service] = lambda: mock_report_service
    app.dependency_overrides[get_risk_analysis_service] = lambda: mock_risk_service

    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/report_abc/risk-analysis")
        assert res.status_code == 200
        assert res.json()["success"] is True
        assert "triggered" in res.json()["message"].lower()

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_report_risks_success():
    mock_user = UserInDB(
        id="user_123",
        email="test@nura.com",
        password_hash="...",
        full_name="Test Patient",
        role=UserRole.PATIENT,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    mock_report = ReportInDB(
        id="report_abc",
        patient_id="user_123",
        uploaded_by="user_123",
        report_type=ReportType.BLOOD_TEST,
        file_url="http://storage/report.pdf",
        processing_status=ProcessingStatus.COMPLETED,
        risk_level=RiskLevel.LOW,
        overall_risk="MEDIUM",
        risk_score=25.0,
        risk_findings=[{"finding_name": "Thyroid Rule", "severity": "MEDIUM", "explanation": "TSH is high"}],
        recommendations=[{"recommendation_type": "Consult physician", "description": "Consult doc", "urgency": "SOON", "disclaimer": "..."}],
        clinical_flags=["THYROID_ABNORMALITY"],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    mock_report_service = MagicMock()
    mock_report_service.get_report_by_id = AsyncMock(return_value=mock_report)

    # Inject overrides
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_report_service] = lambda: mock_report_service

    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/report_abc/risk")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["overall_risk"] == "MEDIUM"
        assert data["risk_score"] == 25.0
        assert len(data["risk_findings"]) == 1
        assert data["risk_findings"][0]["finding_name"] == "Thyroid Rule"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_risk_telemetry_forbidden():
    mock_patient_user = UserInDB(
        id="user_123",
        email="test@nura.com",
        password_hash="...",
        full_name="Test Patient",
        role=UserRole.PATIENT,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    app.dependency_overrides[get_current_user] = lambda: mock_patient_user

    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/risk/statistics")
        # Should reject patient access
        assert res.status_code == 403

    app.dependency_overrides.clear()
