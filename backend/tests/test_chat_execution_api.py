"""
Nura - Chat Execution API Integration Tests
Tests execution route connectivity, RBAC controls, and session stats validation.
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
    get_chat_execution_service,
    get_chat_message_repository,
)
from app.models.user import UserInDB, UserRole, AuthProvider
from app.models.chat import (
    ChatSessionInDB,
    ChatMessageInDB,
    SessionStatus,
    MessageRole,
)
from app.schemas.chat import (
    ChatExecutionResponse,
    ChatSessionStatisticsResponse,
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
def mock_auth_service():
    service = MagicMock()
    def require_role_impl(user, role):
        if role == UserRole.ADMIN and user.role != UserRole.ADMIN:
            raise PermissionError("Admin role required")
    service.require_role = require_role_impl
    return service


def test_execute_message_success(client, patient_user):
    mock_exec_service = AsyncMock()
    mock_response = ChatExecutionResponse(
        assistant_message="Drink water and rest.",
        agent_used="SymptomAgent",
        citations=[],
        usage={"total_tokens": 45},
        latency_ms=450.0,
        cost=0.0001
    )
    mock_exec_service.execute_chat_message = AsyncMock(return_value=mock_response)

    app.dependency_overrides[get_current_user] = lambda: patient_user
    app.dependency_overrides[get_chat_execution_service] = lambda: mock_exec_service

    payload = {
        "session_id": "507f1f77bcf86cd799439080",
        "message": "I have been feeling dizzy."
    }
    response = client.post("/api/v1/chat/message/execute", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["success"] is True
    assert data["data"]["assistant_message"] == "Drink water and rest."
    assert data["data"]["agent_used"] == "SymptomAgent"


def test_get_session_statistics_success(client, patient_user):
    session = ChatSessionInDB(
        id="507f1f77bcf86cd799439080",
        patient_id=patient_user.id,
        title="Checkup",
        status=SessionStatus.ACTIVE,
        session_type="ai_chat",
        active=True,
        last_message_at=utc_now(),
        message_count=2,
        total_tokens=150,
        total_cost=0.005,
        last_agent_used="MemoryAgent",
        pinned=False,
        archived=False,
        metadata={},
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    
    mock_session_service = AsyncMock()
    mock_session_service.get_session_by_id = AsyncMock(return_value=session)
    
    # Mock message repo for statistics calculation
    mock_message_repo = AsyncMock()
    mock_messages = [
        ChatMessageInDB(
            id="msg1",
            session_id="507f1f77bcf86cd799439080",
            patient_id=patient_user.id,
            role=MessageRole.USER,
            content="Hello",
            citations=[],
            attachments=[],
            token_usage={},
            deleted=False,
            created_at=utc_now()
        ),
        ChatMessageInDB(
            id="msg2",
            session_id="507f1f77bcf86cd799439080",
            patient_id=patient_user.id,
            role=MessageRole.ASSISTANT,
            content="Hi",
            citations=[],
            attachments=[],
            token_usage={"total_tokens": 150},
            latency_ms=600,
            deleted=False,
            created_at=utc_now()
        )
    ]
    mock_message_repo.get_by_session_id = AsyncMock(return_value=mock_messages)

    app.dependency_overrides[get_current_user] = lambda: patient_user
    app.dependency_overrides[get_chat_session_service] = lambda: mock_session_service
    app.dependency_overrides[get_chat_message_repository] = lambda: mock_message_repo

    response = client.get(f"/api/v1/chat/session/{session.id}/statistics")
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["data"]["message_count"] == 2
    assert data["data"]["total_tokens"] == 150
    assert data["data"]["total_cost"] == 0.005
    assert data["data"]["average_latency"] == 600.0
    assert data["data"]["last_agent_used"] == "MemoryAgent"


def test_get_session_statistics_forbidden(client, patient_user):
    session = ChatSessionInDB(
        id="507f1f77bcf86cd799439080",
        patient_id="different_patient",  # Forbidden owner
        title="Checkup",
        status=SessionStatus.ACTIVE,
        session_type="ai_chat",
        active=True,
        last_message_at=utc_now(),
        message_count=0,
        total_tokens=0,
        total_cost=0.0,
        pinned=False,
        archived=False,
        metadata={},
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    
    mock_session_service = AsyncMock()
    mock_session_service.get_session_by_id = AsyncMock(return_value=session)

    app.dependency_overrides[get_current_user] = lambda: patient_user
    app.dependency_overrides[get_chat_session_service] = lambda: mock_session_service
    app.dependency_overrides[get_chat_message_repository] = lambda: AsyncMock()

    response = client.get(f"/api/v1/chat/session/{session.id}/statistics")
    assert response.status_code == 404

