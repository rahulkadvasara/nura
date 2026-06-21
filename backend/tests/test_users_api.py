import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

from app.main import app
from app.core.dependencies import get_current_user, get_user_service
from app.models.user import UserInDB, UserRole, AuthProvider
from app.models.preferences import NotificationPreferencesInDB

from datetime import datetime, timezone

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

@pytest.fixture
def client():
    app.dependency_overrides.clear()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def test_user():
    now = utc_now()
    return UserInDB(
        id="507f1f77bcf86cd799439011",
        email="test@example.com",
        password_hash="hashed",
        full_name="Test User",
        role=UserRole.PATIENT,
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True,
        created_at=now,
        updated_at=now
    )

@pytest.fixture
def test_prefs():
    return NotificationPreferencesInDB(
        id="507f1f77bcf86cd799439099",
        user_id="507f1f77bcf86cd799439011",
        email_enabled=True,
        appointment_enabled=True,
        reminder_enabled=True,
        report_enabled=True,
        marketing_enabled=False
    )

@pytest.fixture
def mocks(test_user, test_prefs):
    user_svc = AsyncMock()
    user_svc.to_response = MagicMock(side_effect=lambda u: u)
    
    user_svc.update_user.return_value = test_user
    user_svc.get_user_preferences.return_value = test_prefs
    user_svc.update_user_preferences.return_value = test_prefs

    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[get_user_service] = lambda: user_svc
    
    yield user_svc
    
    app.dependency_overrides.clear()

def test_get_profile(client, mocks, test_user):
    response = client.get("/api/v1/users/profile")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"

def test_update_profile(client, mocks, test_user):
    response = client.put(
        "/api/v1/users/profile",
        json={"full_name": "Updated Name", "phone": "1234567890"}
    )
    assert response.status_code == 200

def test_get_preferences(client, mocks):
    response = client.get("/api/v1/users/preferences")
    assert response.status_code == 200
    data = response.json()
    assert data["email_enabled"] is True

def test_update_preferences(client, mocks):
    response = client.put(
        "/api/v1/users/preferences",
        json={"email_enabled": False, "marketing_enabled": True}
    )
    assert response.status_code == 200


