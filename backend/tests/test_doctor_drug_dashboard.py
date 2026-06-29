import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.core.dependencies import get_current_user, get_medication_validation_service, get_drug_explanation_service
from app.models.user import UserRole, UserInDB, AuthProvider

@pytest.fixture
def client():
    app.dependency_overrides.clear()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def test_doctor():
    return UserInDB(
        id="507f1f77bcf86cd799439011",
        email="doctor@example.com",
        password_hash="hashed_doctor",
        full_name="Dr. Jane",
        role=UserRole.DOCTOR,
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True
    )

@pytest.fixture
def test_patient():
    return UserInDB(
        id="507f1f77bcf86cd799439012",
        email="patient@example.com",
        password_hash="hashed_patient",
        full_name="Jane Patient",
        role=UserRole.PATIENT,
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True
    )

def test_get_doctor_drug_safety_success(client, test_doctor):
    """Test retrieving clinician safety dashboard details successfully as a doctor"""
    app.dependency_overrides[get_current_user] = lambda: test_doctor

    mock_val_service = AsyncMock()
    mock_val_service.collector = AsyncMock()
    mock_val_service.collector.collect = AsyncMock(return_value=["Warfarin", "Aspirin"])
    mock_val_service.validate_medications = AsyncMock(return_value={
        "severity": "HIGH",
        "decision": "BLOCK",
        "recommendations": ["Avoid combination due to bleeding risk"],
        "detected_interactions": []
    })
    app.dependency_overrides[get_medication_validation_service] = lambda: mock_val_service

    mock_explain_service = AsyncMock()
    mock_explain_service.explain_safety = AsyncMock(return_value={
        "doctor_explanation": "Critical bleeding risk.",
        "precautions": "Avoid alcohol, monitor INR."
    })
    app.dependency_overrides[get_drug_explanation_service] = lambda: mock_explain_service
        
    response = client.get("/api/v1/ai/drug/doctor/60d5ec4931a23861245abcde")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert "interaction_details" in data["data"]
    assert "recommendations" in data["data"]
    assert data["data"]["doctor_explanation"] == "Critical bleeding risk."


def test_get_doctor_drug_safety_forbidden_for_patient(client, test_patient):
    """Test that a patient cannot access the doctor clinical safety endpoint"""
    app.dependency_overrides[get_current_user] = lambda: test_patient

    response = client.get("/api/v1/ai/drug/doctor/60d5ec4931a23861245abcde")

    assert response.status_code == status.HTTP_403_FORBIDDEN
