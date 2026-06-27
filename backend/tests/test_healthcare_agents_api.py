"""
Nura Backend - Healthcare Agents REST API Integration Tests
Verifies Healthcare Agent admin endpoints: request validation, RBAC guards, and response schema structure.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock

from app.main import app
from app.core.dependencies import (
    get_current_user,
    get_auth_service,
    get_report_analysis_agent,
    get_drug_interaction_agent,
    get_doctor_recommendation_agent,
)
from app.models.user import UserInDB, UserRole, AuthProvider
from app.agents.base.response import AgentResponse
from app.agents.healthcare.schemas import (
    ReportAnalysisAgentResponse,
    DrugInteractionAgentResponse,
    DoctorRecommendationAgentResponse,
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
        if user.role == UserRole.DOCTOR and required_role in (UserRole.DOCTOR, UserRole.PATIENT):
            return
        if user.role == UserRole.PATIENT and required_role == UserRole.PATIENT:
            return
        raise PermissionError("Forbidden")

    auth_svc.require_role = mock_require_role
    app.dependency_overrides[get_auth_service] = lambda: auth_svc
    return auth_svc


def _make_mock_report_agent() -> MagicMock:
    """Build a mock ReportAnalysisAgent with a valid run() response"""
    agent = MagicMock()
    mock_response = ReportAnalysisAgentResponse(
        summary="Your cholesterol report LDL level is elevated.",
        key_findings=["LDL is 130 mg/dL"],
        abnormal_values=[{"metric": "LDL", "value": "130", "normal_range": "<100", "status": "HIGH"}],
        trend_analysis=[],
        recommendations=["Eat healthy foods."],
        citations=[{"source": "report_1", "text": "LDL value: 130", "score": 0.99}],
        metadata={"total_latency_ms": 100.0, "groq_latency_ms": 40.0},
        usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
    )
    agent.run = AsyncMock(return_value=AgentResponse(
        success=True,
        message="Execution completed successfully",
        response=mock_response,
        execution_time=100.0,
        agent_name="ReportAnalysisAgent"
    ))
    return agent


def _make_mock_drug_agent() -> MagicMock:
    """Build a mock DrugInteractionAgent with a valid run() response"""
    agent = MagicMock()
    mock_response = DrugInteractionAgentResponse(
        interaction_found=True,
        severity="HIGH",
        interaction_summary="Aspirin and Ibuprofen together increase bleeding risk.",
        warnings=["Bleeding risk warning"],
        alternatives=["Acetaminophen"],
        citations=[{"source": "drug_database", "text": "Aspirin/Ibuprofen warning", "score": 0.95}],
        metadata={},
        usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
    )
    agent.run = AsyncMock(return_value=AgentResponse(
        success=True,
        message="Execution completed successfully",
        response=mock_response,
        execution_time=100.0,
        agent_name="DrugInteractionAgent"
    ))
    return agent


def _make_mock_doctor_agent() -> MagicMock:
    """Build a mock DoctorRecommendationAgent with a valid run() response"""
    agent = MagicMock()
    mock_response = DoctorRecommendationAgentResponse(
        recommended_doctors=[
            {
                "doctor_id": "doc-1",
                "full_name": "Dr. Smith",
                "specialization": "Cardiology",
                "hospital": "Nura Gen Hospital",
                "experience_years": 10,
                "languages": ["English"],
                "availability": "Monday 9-12",
                "match_reason": "Close by specialist."
            }
        ],
        reasoning="Patient requires cardiology matching.",
        matching_specialization="Cardiology",
        confidence=0.98,
        metadata={},
        usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
    )
    agent.run = AsyncMock(return_value=AgentResponse(
        success=True,
        message="Execution completed successfully",
        response=mock_response,
        execution_time=100.0,
        agent_name="DoctorRecommendationAgent"
    ))
    return agent


def test_healthcare_agent_endpoints_patient_forbidden(client, mocks, patient_user):
    """Confirm patient users receive 403 on all healthcare agent administrative routes"""
    app.dependency_overrides[get_current_user] = lambda: patient_user

    for path in [
        "/api/v1/ai/agents/report/test",
        "/api/v1/ai/agents/drug/test",
        "/api/v1/ai/agents/doctor/test",
    ]:
        res = client.post(path, json={"query": "test"})
        assert res.status_code == status.HTTP_403_FORBIDDEN, (
            f"Expected 403 for patient on {path}, got {res.status_code}"
        )

    res_stats = client.get("/api/v1/ai/agents/healthcare/statistics")
    assert res_stats.status_code == status.HTTP_403_FORBIDDEN


def test_report_agent_test_success(client, mocks, admin_user):
    """Confirm admin can invoke ReportAnalysisAgent and receive a valid response"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_report_analysis_agent] = _make_mock_report_agent

    payload = {"query": "Analyze my report"}
    response = client.post("/api/v1/ai/agents/report/test", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "abnormal_values" in data
    assert "citations" in data
    assert data["abnormal_values"][0]["metric"] == "LDL"


def test_drug_agent_test_success(client, mocks, admin_user):
    """Confirm admin can invoke DrugInteractionAgent and receive a valid response"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_drug_interaction_agent] = _make_mock_drug_agent

    payload = {"query": "Aspirin with Ibuprofen"}
    response = client.post("/api/v1/ai/agents/drug/test", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "interaction_summary" in data
    assert data["interaction_found"] is True
    assert data["severity"] == "HIGH"


def test_doctor_agent_test_success(client, mocks, admin_user):
    """Confirm admin can invoke DoctorRecommendationAgent and receive a valid response"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_doctor_recommendation_agent] = _make_mock_doctor_agent

    payload = {"query": "Cardiologist near me"}
    response = client.post("/api/v1/ai/agents/doctor/test", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "recommended_doctors" in data
    assert len(data["recommended_doctors"]) == 1
    assert data["recommended_doctors"][0]["full_name"] == "Dr. Smith"
    assert data["matching_specialization"] == "Cardiology"


def test_healthcare_agents_statistics_success(client, mocks, admin_user):
    """Confirm admin can fetch healthcare agents telemetry statistics successfully"""
    app.dependency_overrides[get_current_user] = lambda: admin_user

    from app.agents.healthcare.telemetry import get_healthcare_agents_telemetry
    get_healthcare_agents_telemetry().reset()

    response = client.get("/api/v1/ai/agents/healthcare/statistics")
    assert response.status_code == 200

    data = response.json()
    assert "ReportAnalysisAgent" in data
    assert "DrugInteractionAgent" in data
    assert "DoctorRecommendationAgent" in data
    for agent_stats in data.values():
        assert agent_stats["execution_count"] == 0
        assert agent_stats["total_tokens"] == 0
