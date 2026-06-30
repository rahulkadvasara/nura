"""
Nura - Chat API Integration Tests
Tests route connectivity, RBAC controls, and CRUD validation on chat endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from app.main import app
from app.core.dependencies import (
    get_current_user,
    get_auth_service,
    get_chat_session_service,
    get_chat_message_service,
)
from app.models.user import UserInDB, UserRole, AuthProvider
from app.models.chat import (
    ChatSessionInDB,
    ChatMessageInDB,
    SessionStatus,
    SessionType,
    MessageRole,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.fixture(autouse=True)
def clean_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    """Build TestClient for router endpoint tests"""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def patient_user():
    return UserInDB(
        id="507f1f77bcf86cd799439001",
        email="patient@example.com",
        password_hash="hashed",
        full_name="John Patient",
        role=UserRole.PATIENT,
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True,
        created_at=utc_now(),
        updated_at=utc_now(),
    )


@pytest.fixture
def doctor_user():
    return UserInDB(
        id="507f1f77bcf86cd799439002",
        email="doctor@example.com",
        password_hash="hashed",
        full_name="Dr. Doctor",
        role=UserRole.DOCTOR,
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True,
        created_at=utc_now(),
        updated_at=utc_now(),
    )


@pytest.fixture
def admin_user():
    return UserInDB(
        id="507f1f77bcf86cd799439003",
        email="admin@example.com",
        password_hash="hashed",
        full_name="Admin Administrator",
        role=UserRole.ADMIN,
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True,
        created_at=utc_now(),
        updated_at=utc_now(),
    )


@pytest.fixture
def mock_auth_service():
    """Mock auth service to avoid MongoDB dependency in require_role"""
    service = MagicMock()
    def require_role_impl(user, role):
        if role == UserRole.ADMIN and user.role != UserRole.ADMIN:
            raise PermissionError("Admin role required")
        if role == UserRole.DOCTOR and user.role != UserRole.DOCTOR:
            raise PermissionError("Doctor role required")
    service.require_role = require_role_impl
    return service


@pytest.fixture
def sample_session_model():
    return ChatSessionInDB(
        id="507f1f77bcf86cd799439080",
        patient_id="507f1f77bcf86cd799439001",
        title="General Session",
        description="General description",
        status=SessionStatus.ACTIVE,
        session_type=SessionType.AI_CHAT,
        active=True,
        last_message_at=utc_now(),
        message_count=0,
        total_tokens=0,
        total_cost=0.0,
        last_agent_used=None,
        pinned=False,
        archived=False,
        metadata={},
        created_at=utc_now(),
        updated_at=utc_now(),
    )


@pytest.fixture
def sample_message_model():
    return ChatMessageInDB(
        id="507f1f77bcf86cd799439090",
        session_id="507f1f77bcf86cd799439080",
        patient_id="507f1f77bcf86cd799439001",
        role=MessageRole.USER,
        content="Hello Nura",
        citations=[],
        attachments=[],
        token_usage={},
        latency_ms=None,
        metadata={},
        deleted=False,
        created_at=utc_now(),
        edited_at=None,
    )


def test_create_session_success(client, patient_user, sample_session_model):
    mock_service = AsyncMock()
    mock_service.create_session = AsyncMock(return_value=sample_session_model)
    mock_service.to_response = MagicMock(return_value=sample_session_model)

    app.dependency_overrides[get_current_user] = lambda: patient_user
    app.dependency_overrides[get_chat_session_service] = lambda: mock_service

    payload = {
        "patient_id": patient_user.id,
        "title": "General Session",
        "description": "General description",
        "session_type": "ai_chat",
    }
    response = client.post("/api/v1/chat/session", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == "507f1f77bcf86cd799439080"


def test_create_session_forbidden_for_other_patient(client, patient_user):
    mock_service = AsyncMock()
    app.dependency_overrides[get_current_user] = lambda: patient_user
    app.dependency_overrides[get_chat_session_service] = lambda: mock_service

    payload = {
        "patient_id": "other_patient_id",
        "title": "Other Session",
    }
    response = client.post("/api/v1/chat/session", json=payload)
    assert response.status_code == 403


def test_list_sessions_success(client, patient_user, sample_session_model):
    mock_service = AsyncMock()
    mock_service.list_sessions_by_patient = AsyncMock(return_value=[sample_session_model])
    mock_service.to_response = MagicMock(return_value=sample_session_model)

    app.dependency_overrides[get_current_user] = lambda: patient_user
    app.dependency_overrides[get_chat_session_service] = lambda: mock_service

    response = client.get("/api/v1/chat/sessions")
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]["sessions"]) == 1


def test_get_session_details(client, patient_user, sample_session_model):
    mock_service = AsyncMock()
    mock_service.get_session_by_id = AsyncMock(return_value=sample_session_model)
    mock_service.to_response = MagicMock(return_value=sample_session_model)

    app.dependency_overrides[get_current_user] = lambda: patient_user
    app.dependency_overrides[get_chat_session_service] = lambda: mock_service

    response = client.get(f"/api/v1/chat/session/{sample_session_model.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["data"]["title"] == "General Session"


def test_update_session_details(client, patient_user, sample_session_model):
    mock_service = AsyncMock()
    mock_service.get_session_by_id = AsyncMock(return_value=sample_session_model)
    mock_service.update_session = AsyncMock(return_value=sample_session_model)
    mock_service.to_response = MagicMock(return_value=sample_session_model)

    app.dependency_overrides[get_current_user] = lambda: patient_user
    app.dependency_overrides[get_chat_session_service] = lambda: mock_service

    response = client.patch(f"/api/v1/chat/session/{sample_session_model.id}", json={"title": "Updated Title"})
    assert response.status_code == 200


def test_delete_session_details(client, patient_user, sample_session_model):
    mock_service = AsyncMock()
    mock_service.get_session_by_id = AsyncMock(return_value=sample_session_model)
    mock_service.delete_session = AsyncMock(return_value=True)

    app.dependency_overrides[get_current_user] = lambda: patient_user
    app.dependency_overrides[get_chat_session_service] = lambda: mock_service

    response = client.delete(f"/api/v1/chat/session/{sample_session_model.id}")
    assert response.status_code == 200


def test_post_message_success(client, patient_user, sample_message_model):
    mock_service = AsyncMock()
    mock_service.create_message = AsyncMock(return_value=sample_message_model)
    mock_service.to_response = MagicMock(return_value=sample_message_model)

    app.dependency_overrides[get_current_user] = lambda: patient_user
    app.dependency_overrides[get_chat_message_service] = lambda: mock_service

    payload = {
        "session_id": "507f1f77bcf86cd799439080",
        "patient_id": patient_user.id,
        "role": "USER",
        "content": "Hello Nura",
    }
    response = client.post("/api/v1/chat/message", json=payload)
    assert response.status_code == 201


def test_get_statistics_admin_authorized(client, admin_user, mock_auth_service):
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service

    # Mock database count results
    mock_db = MagicMock()
    mock_db.chat_sessions.count_documents = AsyncMock(return_value=10)
    mock_db.chat_messages.count_documents = AsyncMock(return_value=50)
    
    from app.db.mongodb import mongodb_connection
    mongodb_connection.database = mock_db

    response = client.get("/api/v1/chat/statistics")
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["data"]["sessions_created"] == 10
    assert data["data"]["messages_created"] == 50


def test_get_statistics_patient_forbidden(client, patient_user, mock_auth_service):
    app.dependency_overrides[get_current_user] = lambda: patient_user
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service

    response = client.get("/api/v1/chat/statistics")
    assert response.status_code == 403
