"""
Nura Backend - AI Orchestrator Execution REST API Integration Tests
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock

from app.main import app
from app.core.dependencies import (
    get_current_user,
    get_auth_service,
    get_multi_agent_orchestrator,
)
from app.models.user import UserInDB, UserRole, AuthProvider
from app.schemas.orchestrator import StandardResponseContract


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


def _make_mock_orchestrator() -> MagicMock:
    """Build mock MultiAgentOrchestrator"""
    orchestrator = MagicMock()
    mock_response = StandardResponseContract(
        success=True,
        agent="MedicalKnowledgeAgent",
        intent="MEDICAL_KNOWLEDGE",
        response="Unified system response.",
        citations=[],
        metadata={},
        usage={"total_tokens": 100},
        execution_trace=["__start__", "initialize_state", "router_agent", "MedicalKnowledgeAgent", "__finish__"],
        execution_time=50.0,
        cost=0.0002,
        warnings=[]
    )
    orchestrator.execute = AsyncMock(return_value=mock_response)
    return orchestrator


def test_execute_pipeline_requires_authentication(client):
    """Confirm unauthenticated users receive 401/403 on execution endpoint"""
    # Missing credentials -> FastAPI HTTPBearer throws 403 Forbidden
    res = client.post("/api/v1/ai/execute", json={"query": "test"})
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # Invalid credentials -> get_current_user JWT decode fails -> 401 Unauthorized
    res_invalid = client.post(
        "/api/v1/ai/execute",
        json={"query": "test"},
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert res_invalid.status_code == status.HTTP_401_UNAUTHORIZED


def test_execute_pipeline_success_patient(client, mocks, patient_user):
    """Confirm patients can invoke execute pipeline and receive standard contract response"""
    app.dependency_overrides[get_current_user] = lambda: patient_user
    app.dependency_overrides[get_multi_agent_orchestrator] = _make_mock_orchestrator

    payload = {"query": "Tell me about cholesterol", "patient_id": "patient-123"}
    response = client.post("/api/v1/ai/execute", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["agent"] == "MedicalKnowledgeAgent"
    assert data["intent"] == "MEDICAL_KNOWLEDGE"
    assert data["response"] == "Unified system response."


def test_debug_endpoint_patient_forbidden(client, mocks, patient_user):
    """Confirm patient users receive 403 on debug execution route"""
    app.dependency_overrides[get_current_user] = lambda: patient_user

    res = client.post("/api/v1/ai/execution/debug", json={"query": "test"})
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_debug_endpoint_success_admin(client, mocks, admin_user):
    """Confirm admin can run debug route and receive standard contract response"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_multi_agent_orchestrator] = _make_mock_orchestrator

    payload = {"query": "Tell me about cholesterol"}
    response = client.post("/api/v1/ai/execution/debug", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["execution_trace"] is not None


def test_get_statistics_success_admin(client, mocks, admin_user):
    """Confirm admin can retrieve telemetry stats"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    
    from app.services.multi_agent_orchestrator import get_multi_agent_telemetry
    get_multi_agent_telemetry().reset()

    response = client.get("/api/v1/ai/execution/statistics")
    assert response.status_code == 200
    data = response.json()
    assert data["total_executions"] == 0
