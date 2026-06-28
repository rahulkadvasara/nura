import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock

from app.main import app
from app.core.dependencies import (
    get_current_user,
    get_auth_service,
    get_medication_validation_service,
    get_drug_explanation_service,
)
from app.models.user import UserInDB, UserRole, AuthProvider


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


def test_explain_endpoints_rbac_patient_forbidden(client, mock_auth, patient_user):
    app.dependency_overrides[get_current_user] = lambda: patient_user

    # POST /drug/explain forbidden
    res = client.post("/api/v1/ai/drug/explain", json={"patient_id": "pat-123", "incoming_medications": ["Aspirin"]})
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # GET /drug/ai/statistics forbidden
    res_stats = client.get("/api/v1/ai/drug/ai/statistics")
    assert res_stats.status_code == status.HTTP_403_FORBIDDEN


def test_explain_medications_api_success(client, mock_auth, admin_user):
    app.dependency_overrides[get_current_user] = lambda: admin_user

    # Mock Validation Service
    mock_val_service = AsyncMock()
    mock_val_service.validate_medications.return_value = {
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
        "latency_ms": 10.0
    }
    app.dependency_overrides[get_medication_validation_service] = lambda: mock_val_service

    # Mock Explanation Service
    mock_explain_service = AsyncMock()
    mock_explain_service.explain_safety.return_value = {
        "patient_explanation": "Simple patient text warning",
        "doctor_explanation": "Pharmacological doctor text details",
        "precautions": "Precautions: do this",
        "summary": "AI summary line",
        "fallback_used": False,
        "latency_ms": 15.0,
        "prompt_tokens": 12,
        "completion_tokens": 24,
        "estimated_cost": 0.0001
    }
    app.dependency_overrides[get_drug_explanation_service] = lambda: mock_explain_service

    payload = {
        "patient_id": "patient-123",
        "incoming_medications": ["Warfarin"]
    }
    res = client.post("/api/v1/ai/drug/explain", json=payload)

    assert res.status_code == 200
    data = res.json()
    assert data["severity"] == "HIGH"
    assert data["patient_explanation"] == "Simple patient text warning"
    assert data["doctor_explanation"] == "Pharmacological doctor text details"
    assert data["precautions"] == "Precautions: do this"
    assert data["summary"] == "AI summary line"
    assert data["fallback_used"] is False
    assert data["token_usage"]["prompt_tokens"] == 12
    assert data["token_usage"]["completion_tokens"] == 24
    assert data["estimated_cost"] == 0.0001


def test_get_drug_ai_statistics(client, mock_auth, admin_user):
    app.dependency_overrides[get_current_user] = lambda: admin_user

    mock_explain_service = MagicMock()
    mock_telemetry = MagicMock()
    mock_telemetry.get_statistics.return_value = {
        "explanation_requests": 5,
        "successful_generations": 4,
        "fallback_executions": 1,
        "prompt_tokens": 100,
        "completion_tokens": 200,
        "total_tokens": 300,
        "estimated_cost": 0.00012,
        "avg_latency_ms": 25.5,
        "model_usage": {"llama": 4}
    }
    mock_explain_service.telemetry = mock_telemetry
    app.dependency_overrides[get_drug_explanation_service] = lambda: mock_explain_service

    res = client.get("/api/v1/ai/drug/ai/statistics")
    assert res.status_code == 200
    data = res.json()
    assert data["explanation_requests"] == 5
    assert data["fallback_executions"] == 1
    assert data["total_tokens"] == 300
    assert data["avg_latency_ms"] == 25.5
