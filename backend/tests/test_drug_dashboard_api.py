import pytest
from datetime import datetime, timezone
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

from app.main import app
from app.core.dependencies import get_current_user, get_auth_service
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
def mock_auth():
    auth_svc = MagicMock()
    auth_svc.require_role = lambda user, role: None
    return auth_svc

def test_get_drug_validation_history_success(client, test_user):
    """Test retrieving patient validation history successfully"""
    app.dependency_overrides[get_current_user] = lambda: test_user

    mock_history_item = {
        "_id": "60d5ec4931a23861245abcde",
        "patient_id": str(test_user.id),
        "incoming_medications": ["Aspirin"],
        "collected_medications": ["Ibuprofen"],
        "decision": "WARNING",
        "severity": "LOW",
        "recommendations": ["Take with water"],
        "detected_interactions": [],
        "source": "api",
        "override_reason": None,
        "overridden_by": None,
        "latency_ms": 12.5,
        "created_at": datetime.now(timezone.utc)
    }

    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=[mock_history_item])

    mock_collection = AsyncMock()
    mock_collection.find = AsyncMock(return_value=mock_cursor)

    mock_db = AsyncMock()
    mock_db.drug_validation_history = mock_collection

    with patch("app.api.v1.ai.get_database", return_value=mock_db):
        response = client.get(f"/api/v1/ai/drug/history/{test_user.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["decision"] == "WARNING"


def test_get_drug_dashboard_statistics_admin(client, admin_user, mock_auth):
    """Test retrieving drug safety dashboard metrics as administrator"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_auth_service] = lambda: mock_auth

    mock_db = AsyncMock()
    mock_db.drug_validation_history = AsyncMock()
    mock_db.drug_validation_history.count_documents = AsyncMock(return_value=5)

    with patch("app.api.v1.ai.get_database", return_value=mock_db):
        response = client.get("/api/v1/ai/drug/dashboard/statistics")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["validations"] == 5
        assert data["data"]["highest_severity_distribution"]["HIGH"] == 5
