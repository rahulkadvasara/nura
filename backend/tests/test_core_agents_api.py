"""
Nura Backend - Core Agents REST API Integration Tests
Verifies Core Agent admin endpoints: request validation, RBAC guards, and response schema structure.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch

from app.main import app
from app.core.dependencies import (
    get_current_user,
    get_auth_service,
    get_medical_knowledge_agent,
    get_symptom_agent,
    get_memory_agent,
)
from app.models.user import UserInDB, UserRole, AuthProvider
from app.agents.base.response import AgentResponse
from app.agents.core.schemas import (
    MedicalKnowledgeAgentResponse,
    SymptomAgentResponse,
    MemoryAgentResponse,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

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
        if user.role == UserRole.DOCTOR and required_role in (UserRole.DOCTOR, UserRole.PATIENT):
            return
        if user.role == UserRole.PATIENT and required_role == UserRole.PATIENT:
            return
        raise PermissionError("Forbidden")

    auth_svc.require_role = mock_require_role
    app.dependency_overrides[get_auth_service] = lambda: auth_svc
    return auth_svc


def _make_mock_medical_agent() -> MagicMock:
    """Build a mock MedicalKnowledgeAgent with a valid run() response"""
    agent = MagicMock()
    mock_response = MedicalKnowledgeAgentResponse(
        answer="Diabetes is managed via lifestyle changes and medication.",
        citations=[{"source": "clinical_guidelines", "text": "Diabetes management...", "score": 0.95}],
        confidence=0.90,
        sources=["medical_knowledge"],
        metadata={"retrieval_latency_ms": 50.0},
        usage={"prompt_tokens": 150, "completion_tokens": 50, "total_tokens": 200}
    )
    agent.run = AsyncMock(return_value=AgentResponse(
        success=True,
        message="Execution completed successfully",
        response=mock_response,
        execution_time=120.0,
        agent_name="MedicalKnowledgeAgent"
    ))
    return agent


def _make_mock_symptom_agent() -> MagicMock:
    """Build a mock SymptomAgent with a valid run() response"""
    agent = MagicMock()
    mock_response = SymptomAgentResponse(
        summary="Chest pain may indicate cardiac or gastrointestinal origin.\n\nDisclaimer: informational purposes only.",
        possible_causes=["Heartburn", "Angina"],
        red_flags=["Chest tightness radiating to arm"],
        recommended_action="Seek medical attention promptly.",
        emergency=False,
        citations=[],
        metadata={},
        usage={"prompt_tokens": 200, "completion_tokens": 80, "total_tokens": 280}
    )
    agent.run = AsyncMock(return_value=AgentResponse(
        success=True,
        message="Execution completed successfully",
        response=mock_response,
        execution_time=100.0,
        agent_name="SymptomAgent"
    ))
    return agent


def _make_mock_memory_agent() -> MagicMock:
    """Build a mock MemoryAgent with a valid run() response"""
    agent = MagicMock()
    mock_response = MemoryAgentResponse(
        memory_summary="Patient has a history of hypertension.",
        conversation_history=[{"role": "user", "content": "what medications am I on?"}],
        patient_summary="Chronic Conditions: Hypertension\nAllergies: Penicillin",
        relevant_context=[{"content": "hypertension management notes", "score": 0.88}],
        metadata={"total_latency_ms": 90.0}
    )
    agent.run = AsyncMock(return_value=AgentResponse(
        success=True,
        message="Execution completed successfully",
        response=mock_response,
        execution_time=90.0,
        agent_name="MemoryAgent"
    ))
    return agent


# ---------------------------------------------------------------------------
# RBAC Guard Tests
# ---------------------------------------------------------------------------

def test_core_agent_endpoints_patient_forbidden(client, mocks, patient_user):
    """Confirm patient users receive 403 on all core agent administrative routes"""
    app.dependency_overrides[get_current_user] = lambda: patient_user

    for path in [
        "/api/v1/ai/agents/medical/test",
        "/api/v1/ai/agents/symptom/test",
        "/api/v1/ai/agents/memory/test",
    ]:
        res = client.post(path, json={"query": "test"})
        assert res.status_code == status.HTTP_403_FORBIDDEN, (
            f"Expected 403 for patient on {path}, got {res.status_code}"
        )

    res_stats = client.get("/api/v1/ai/agents/statistics")
    assert res_stats.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# Medical Knowledge Agent Tests
# ---------------------------------------------------------------------------

def test_medical_agent_test_success(client, mocks, admin_user):
    """Confirm admin can invoke MedicalKnowledgeAgent and receive a valid response"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_medical_knowledge_agent] = _make_mock_medical_agent

    payload = {"query": "How do I manage diabetes mellitus?"}
    response = client.post("/api/v1/ai/agents/medical/test", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "insulin" in data["answer"].lower() or "diabetes" in data["answer"].lower() or "lifestyle" in data["answer"].lower()
    assert "citations" in data
    assert isinstance(data["citations"], list)
    assert "confidence" in data
    assert 0.0 <= data["confidence"] <= 1.0
    assert "sources" in data
    assert "usage" in data


def test_medical_agent_test_missing_query(client, mocks, admin_user):
    """Confirm a missing query body triggers HTTP 422 Unprocessable Entity"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_medical_knowledge_agent] = _make_mock_medical_agent

    response = client.post("/api/v1/ai/agents/medical/test", json={})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_medical_agent_test_empty_query(client, mocks, admin_user):
    """Confirm an empty query string triggers HTTP 422 Unprocessable Entity"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_medical_knowledge_agent] = _make_mock_medical_agent

    response = client.post("/api/v1/ai/agents/medical/test", json={"query": ""})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ---------------------------------------------------------------------------
# Symptom Agent Tests
# ---------------------------------------------------------------------------

def test_symptom_agent_test_success(client, mocks, admin_user):
    """Confirm admin can invoke SymptomAgent and receive a valid response"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_symptom_agent] = _make_mock_symptom_agent

    payload = {"query": "I have sharp chest pain when breathing"}
    response = client.post("/api/v1/ai/agents/symptom/test", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "possible_causes" in data
    assert isinstance(data["possible_causes"], list)
    assert "red_flags" in data
    assert isinstance(data["red_flags"], list)
    assert "recommended_action" in data
    assert "emergency" in data
    assert isinstance(data["emergency"], bool)
    assert "citations" in data
    assert "usage" in data


def test_symptom_agent_test_missing_query(client, mocks, admin_user):
    """Confirm a missing query body triggers HTTP 422 Unprocessable Entity"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_symptom_agent] = _make_mock_symptom_agent

    response = client.post("/api/v1/ai/agents/symptom/test", json={})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ---------------------------------------------------------------------------
# Memory Agent Tests
# ---------------------------------------------------------------------------

def test_memory_agent_test_success(client, mocks, admin_user):
    """Confirm admin can invoke MemoryAgent and receive a valid response"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_memory_agent] = _make_mock_memory_agent

    payload = {"query": "recall my recent messages", "patient_id": "patient-123"}
    response = client.post("/api/v1/ai/agents/memory/test", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "memory_summary" in data
    assert "conversation_history" in data
    assert isinstance(data["conversation_history"], list)
    assert "patient_summary" in data
    assert "relevant_context" in data
    assert isinstance(data["relevant_context"], list)


def test_memory_agent_test_missing_query(client, mocks, admin_user):
    """Confirm a missing query body triggers HTTP 422 Unprocessable Entity"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_memory_agent] = _make_mock_memory_agent

    response = client.post("/api/v1/ai/agents/memory/test", json={})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ---------------------------------------------------------------------------
# Core Agents Statistics Endpoint Test
# ---------------------------------------------------------------------------

def test_core_agents_statistics_success(client, mocks, admin_user):
    """Confirm admin can fetch core agents telemetry statistics successfully"""
    app.dependency_overrides[get_current_user] = lambda: admin_user

    from app.agents.core.telemetry import get_core_agents_telemetry
    get_core_agents_telemetry().reset()

    response = client.get("/api/v1/ai/agents/statistics")
    assert response.status_code == 200

    data = response.json()
    # Telemetry stats returns per-agent breakdown keyed by agent name
    assert "MedicalKnowledgeAgent" in data
    assert "SymptomAgent" in data
    assert "MemoryAgent" in data
    # Each agent entry starts at zero after reset
    for agent_stats in data.values():
        assert agent_stats["execution_count"] == 0
        assert agent_stats["total_tokens"] == 0
