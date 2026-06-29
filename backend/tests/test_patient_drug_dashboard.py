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
def test_user():
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

def test_get_patient_drug_safety_success(client, test_user):
    """Test retrieving patient-friendly drug safety details successfully"""
    app.dependency_overrides[get_current_user] = lambda: test_user

    mock_val_service = AsyncMock()
    mock_val_service.collector = AsyncMock()
    mock_val_service.collector.collect = AsyncMock(return_value=["Aspirin", "Ibuprofen"])
    mock_val_service.validate_medications = AsyncMock(return_value={
        "severity": "LOW",
        "decision": "WARNING",
        "recommendations": ["Take with food"],
        "detected_interactions": []
    })
    app.dependency_overrides[get_medication_validation_service] = lambda: mock_val_service

    mock_explain_service = AsyncMock()
    mock_explain_service.explain_safety = AsyncMock(return_value={
        "patient_explanation": "You are taking Aspirin and Ibuprofen. Both are NSAIDs.",
        "doctor_explanation": "Potential duplicate therapy.",
        "precautions": "Monitor GI side effects."
    })
    app.dependency_overrides[get_drug_explanation_service] = lambda: mock_explain_service
        
    response = client.get(f"/api/v1/ai/drug/patient/{test_user.id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert "active_medications" in data["data"]
    assert data["data"]["severity"] == "LOW"
    assert "NSAIDs" in data["data"]["patient_explanation"]


def test_get_patient_drug_safety_forbidden(client, test_user):
    """Test that a patient cannot access another patient's safety dashboard"""
    app.dependency_overrides[get_current_user] = lambda: test_user

    # Attempt to access a random user ID
    response = client.get("/api/v1/ai/drug/patient/60d5ec4931a23861245abcde")

    assert response.status_code == status.HTTP_403_FORBIDDEN
