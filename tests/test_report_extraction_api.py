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
from app.core.dependencies import get_current_user, get_report_service, get_report_extraction_service
from app.models.user import UserInDB, UserRole
from app.models.report import ReportInDB, ProcessingStatus, ReportType, RiskLevel

# Construct test FastAPI app instance
app = FastAPI()
app.include_router(router)


@pytest.mark.asyncio
async def test_extraction_endpoints_authorized():
    # Mock current active user (patient)
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
    
    # Mock Report record with completed extraction details
    mock_report = ReportInDB(
        id="test_report_id",
        patient_id="test_patient_id",
        uploaded_by="test_patient_id",
        report_type=ReportType.BLOOD_TEST,
        file_url="uploads/reports/test.pdf",
        raw_text="Hemoglobin 14.5",
        normalized_text="Hemoglobin 14.5",
        risk_level=RiskLevel.LOW,
        processing_status=ProcessingStatus.COMPLETED,
        ocr_status="completed",
        ocr_method="digital",
        ocr_average_confidence=0.98,
        page_count=1,
        ocr_pages=[],
        
        # Extraction fields
        document_type="CBC",
        structured_data={
            "patient_information": {"patient_name": "Patient Name", "age": 30},
            "hospital_information": {"hospital": "Core Hospital"}
        },
        entities=[{"text": "Diabetes", "category": "diagnoses"}],
        laboratory_results=[{"test_name": "Hemoglobin", "value": 14.5, "unit": "g/dL", "reference_range": "13.0-17.0", "status": "NORMAL"}],
        medications=[],
        diagnoses=["Diabetes"],
        allergies=[],
        extraction_status="completed",
        extraction_confidence=0.95,
        extraction_version="1.0.0",
        extraction_warnings=[],
        
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    # Mock Services
    mock_service = MagicMock()
    mock_service.get_report_by_id = AsyncMock(return_value=mock_report)
    mock_service.to_response = MagicMock(return_value=mock_report)

    mock_extractor = MagicMock()
    mock_extractor.extract_medical_information = AsyncMock(return_value=mock_report)

    # Override dependencies
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_report_service] = lambda: mock_service
    app.dependency_overrides[get_report_extraction_service] = lambda: mock_extractor
    
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        # 1. Test triggering extraction
        res = await client.post("/test_report_id/extract")
        assert res.status_code == 200
        assert res.json()["success"] is True
        assert "extraction" in res.json()["message"].lower()

        # 2. Test fetching structured details
        res = await client.get("/test_report_id/structured")
        assert res.status_code == 200
        assert res.json()["success"] is True
        assert res.json()["data"]["document_type"] == "CBC"
        assert len(res.json()["data"]["laboratory_results"]) == 1

        # 3. Test fetching entities list
        res = await client.get("/test_report_id/entities")
        assert res.status_code == 200
        assert res.json()["success"] is True
        assert len(res.json()["data"]["entities"]) == 1
        assert res.json()["data"]["entities"][0]["text"] == "Diabetes"

    # Clean overrides
    app.dependency_overrides.clear()
