"""
Nura Backend - Operations Agents REST API Integration Tests
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock

from app.main import app
from app.core.dependencies import (
    get_current_user,
    get_auth_service,
    get_reminder_agent,
    get_appointment_agent,
)
from app.models.user import UserInDB, UserRole, AuthProvider
from app.agents.base.response import AgentResponse
from app.agents.operations.schemas import (
    ReminderAgentResponse,
    AppointmentAgentResponse,
)


@pytest.fixture
def client():
    """Build TestClient instance for API invoke tests"""
    app.dependency_overrides.clear()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user():
    """Mock Admin User"""
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
    """Mock Patient User"""
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
def mocks():
    """Mock AuthService to bypass real database connection check"""
    auth_svc = MagicMock()

    def mock_require_role(user, required_role):
        if user.role == UserRole.ADMIN:
            return
        raise PermissionError("Forbidden")

    auth_svc.require_role = mock_require_role
    app.dependency_overrides[get_auth_service] = lambda: auth_svc
    return auth_svc


def _make_mock_reminder_agent() -> MagicMock:
    """Build mock ReminderAgent"""
    agent = MagicMock()
    mock_response = ReminderAgentResponse(
        status="success",
        action="create_medication_reminder",
        message="Medication reminder successfully created.",
        created_reminder={"title": "Take Aspirin"},
        warnings=[],
        usage={"total_tokens": 150},
        metadata={"patient_id": "patient-123"}
    )
    agent.run = AsyncMock(return_value=AgentResponse(
        success=True,
        message="Success",
        response=mock_response,
        execution_time=50.0,
        agent_name="ReminderAgent"
    ))
    return agent


def _make_mock_appointment_agent() -> MagicMock:
    """Build mock AppointmentAgent"""
    agent = MagicMock()
    mock_response = AppointmentAgentResponse(
        status="success",
        action="book_appointment",
        message="Appointment booked successfully.",
        appointment={"id": "appt-123"},
        usage={"total_tokens": 150},
        metadata={"patient_id": "patient-123"}
    )
    agent.run = AsyncMock(return_value=AgentResponse(
        success=True,
        message="Success",
        response=mock_response,
        execution_time=50.0,
        agent_name="AppointmentAgent"
    ))
    return agent


def test_operations_agent_endpoints_patient_forbidden(client, mocks, patient_user):
    """Confirm patient users receive 403 on all operations agent administrative routes"""
    app.dependency_overrides[get_current_user] = lambda: patient_user

    for path in [
        "/api/v1/ai/agents/reminder/test",
        "/api/v1/ai/agents/appointment/test",
    ]:
        res = client.post(path, json={"query": "test"})
        assert res.status_code == status.HTTP_403_FORBIDDEN

    res_stats = client.get("/api/v1/ai/agents/operations/statistics")
    assert res_stats.status_code == status.HTTP_403_FORBIDDEN


def test_reminder_agent_test_success(client, mocks, admin_user):
    """Confirm admin can invoke ReminderAgent and receive a valid response"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_reminder_agent] = _make_mock_reminder_agent

    payload = {"query": "Create daily reminder for Aspirin at 8 AM", "patient_id": "patient-123"}
    response = client.post("/api/v1/ai/agents/reminder/test", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["action"] == "create_medication_reminder"
    assert data["created_reminder"]["title"] == "Take Aspirin"


def test_appointment_agent_test_success(client, mocks, admin_user):
    """Confirm admin can invoke AppointmentAgent and receive a valid response"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_appointment_agent] = _make_mock_appointment_agent

    payload = {"query": "Book dermatologist slot", "patient_id": "patient-123"}
    response = client.post("/api/v1/ai/agents/appointment/test", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["action"] == "book_appointment"
    assert data["appointment"]["id"] == "appt-123"


def test_operations_agents_statistics_success(client, mocks, admin_user):
    """Confirm admin can fetch operations agents telemetry statistics successfully"""
    app.dependency_overrides[get_current_user] = lambda: admin_user

    from app.agents.operations.telemetry import get_operations_telemetry
    get_operations_telemetry().reset()

    response = client.get("/api/v1/ai/agents/operations/statistics")
    assert response.status_code == 200

    data = response.json()
    assert "ReminderAgent" in data
    assert "AppointmentAgent" in data
    for agent_stats in data.values():
        assert agent_stats["execution_count"] == 0
