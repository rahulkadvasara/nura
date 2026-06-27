import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from app.api.v1.reports import router
from app.core.dependencies import get_current_user, get_report_service, get_document_parser, get_database
from app.models.user import UserInDB, UserRole
from app.models.report import ReportInDB, ProcessingStatus, ReportType, RiskLevel

# Construct test FastAPI app instance
app = FastAPI()
app.include_router(router)


@pytest.fixture
def client():
    return TestClient(app)


def test_reports_api_unauthorized(client):
    # Missing Auth token should reject request (handled by security dependencies)
    res = client.get("/")
    assert res.status_code in (401, 403, 422)


def test_reports_endpoints_with_mock_auth(client):
    # Mock current active user
    mock_user = UserInDB(
        id="test_patient_id",
        email="patient@nura.com",
        password_hash="...",
        role=UserRole.PATIENT,
        is_active=True,
        full_name="Patient Name",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    # Mock Report record
    mock_report = ReportInDB(
        id="test_report_id",
        patient_id="test_patient_id",
        uploaded_by="test_patient_id",
        report_type=ReportType.BLOOD_TEST,
        file_url="uploads/reports/test.pdf",
        raw_text="Extracted text layout data",
        normalized_text="Extracted text layout data",
        risk_level=RiskLevel.LOW,
        processing_status=ProcessingStatus.COMPLETED,
        ocr_status="completed",
        ocr_method="digital",
        ocr_average_confidence=0.98,
        page_count=1,
        ocr_version="1.0.0",
        ocr_pages=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    # Mock Services
    mock_service = MagicMock()
    mock_service.list_reports_by_patient = AsyncMock(return_value=[mock_report])
    mock_service.get_report_by_id = AsyncMock(return_value=mock_report)
    mock_service.to_response = MagicMock(return_value=mock_report)

    mock_parser = MagicMock()
    mock_parser.process_report = AsyncMock(return_value=mock_report)

    # Override dependencies
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_report_service] = lambda: mock_service
    app.dependency_overrides[get_document_parser] = lambda: mock_parser
    
    # 1. Test listing reports
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert "reports" in res.json()["data"]

    # 2. Test status check
    res = client.get("/test_report_id/processing-status")
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["data"]["ocr_status"] == "completed"

    # 3. Test retrieving OCR text
    res = client.get("/test_report_id/ocr")
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["data"]["raw_text"] == "Extracted text layout data"

    # Clean overrides
    app.dependency_overrides.clear()
