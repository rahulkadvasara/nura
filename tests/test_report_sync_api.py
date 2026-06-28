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
from app.core.dependencies import get_current_user, get_report_service, get_report_sync_service, get_report_sync_validator
from app.models.user import UserInDB, UserRole
from app.models.report import ReportInDB, ProcessingStatus, ReportType, RiskLevel

# Construct test FastAPI app instance
app = FastAPI()
app.include_router(router)


@pytest.mark.asyncio
async def test_synchronize_report_endpoint():
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

    mock_sync_service = MagicMock()
    mock_sync_service.synchronize_report = AsyncMock(return_value={"success": True})

    # Inject overrides
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_report_service] = lambda: mock_report_service
    app.dependency_overrides[get_report_sync_service] = lambda: mock_sync_service

    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/report_123/synchronize")
        assert res.status_code == 200
        assert res.json()["success"] is True
        assert "completed" in res.json()["message"].lower()

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_sync_status_endpoint():
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

    mock_validator = MagicMock()
    mock_validator.validate_synchronization = AsyncMock(return_value={"in_sync": True})

    # Inject overrides
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_report_service] = lambda: mock_report_service
    app.dependency_overrides[get_report_sync_validator] = lambda: mock_validator

    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/report_123/sync-status")
        assert res.status_code == 200
        assert res.json()["data"]["in_sync"] is True

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_rebuild_index_forbidden_for_patient():
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
    app.dependency_overrides[get_report_sync_service] = lambda: MagicMock()

    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/synchronization/rebuild")
        # Assert forbidden response
        assert res.status_code == 403

    app.dependency_overrides.clear()
