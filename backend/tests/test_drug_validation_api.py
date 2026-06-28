import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock

from app.main import app
from app.core.dependencies import (
    get_current_user,
    get_auth_service,
    get_medication_validation_service,
)
from app.models.user import UserInDB, UserRole, AuthProvider
from app.services.drug_safety.models import InteractionPairDetail


@pytest.fixture
def client():
    app.dependency_overrides.clear()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user():
    return UserInDB(
        id="507f1f77bcf86cd799439011",
        email="admin@example.com",
        password_hash="hashed_admin",
        full_name="Admin User",
        role=UserRole.ADMIN,
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True
    )


@pytest.fixture
def patient_user():
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


@pytest.fixture
def mock_auth():
    auth_svc = MagicMock()
    def mock_require_role(user, required_role):
        if user.role == UserRole.ADMIN:
            return
        raise PermissionError("Forbidden")
    auth_svc.require_role = mock_require_role
    app.dependency_overrides[get_auth_service] = lambda: auth_svc
    return auth_svc


def test_validation_endpoints_rbac_patient_forbidden(client, mock_auth, patient_user):
    app.dependency_overrides[get_current_user] = lambda: patient_user

    # POST /drug/validate forbidden
    res = client.post("/api/v1/ai/drug/validate", json={"patient_id": "pat-123", "incoming_medications": ["Aspirin"]})
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # GET /drug/validation/statistics forbidden
    res_stats = client.get("/api/v1/ai/drug/validation/statistics")
    assert res_stats.status_code == status.HTTP_403_FORBIDDEN


def test_validate_medications_api_success(client, mock_auth, admin_user):
    app.dependency_overrides[get_current_user] = lambda: admin_user

    mock_service = AsyncMock()
    mock_service.validate_medications.return_value = {
        "collected_medications": ["ASPIRIN"],
        "detected_interactions": [
            {
                "drug_a": "Aspirin",
                "drug_b": "Warfarin",
                "drug_a_normalized": "ASPIRIN",
                "drug_b_normalized": "WARFARIN",
                "severity": "HIGH",
                "description": "Increased bleeding risk"
            }
        ],
        "severity": "HIGH",
        "decision": "BLOCK",
        "recommendations": ["Do not combine Aspirin and Warfarin"],
        "latency_ms": 12.34
    }
    app.dependency_overrides[get_medication_validation_service] = lambda: mock_service

    payload = {
        "patient_id": "patient-123",
        "incoming_medications": ["Warfarin"]
    }
    res = client.post("/api/v1/ai/drug/validate", json=payload)

    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "BLOCK"
    assert data["severity"] == "HIGH"
    assert len(data["detected_interactions"]) == 1
    assert data["detected_interactions"][0]["description"] == "Increased bleeding risk"
    assert data["latency_ms"] == 12.34


def test_get_medication_validation_statistics(client, mock_auth, admin_user):
    app.dependency_overrides[get_current_user] = lambda: admin_user

    from app.services.drug_safety.telemetry import drug_safety_telemetry
    drug_safety_telemetry.reset()
    # Record one dummy validation to make stats non-zero
    drug_safety_telemetry.record_validation("api", "BLOCK", 15.0)

    res = client.get("/api/v1/ai/drug/validation/statistics")
    assert res.status_code == 200
    data = res.json()
    assert data["validation_checks"] == 1
    assert data["blocked_decisions"] == 1
    assert data["validation_avg_latency_ms"] == 15.0
