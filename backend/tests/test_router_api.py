"""
Nura Backend - Router REST API Integration Tests
Verifies Router endpoints request validation, payloads structures, and admin RBAC guards.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.core.dependencies import get_current_user, get_auth_service
from app.models.user import UserInDB, UserRole, AuthProvider
from app.agents.router.telemetry import get_router_telemetry


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


def test_router_endpoints_patient_forbidden(client, mocks, patient_user):
    """Confirm patient users get 403 on Router administrative routes"""
    app.dependency_overrides[get_current_user] = lambda: patient_user
    
    # 1. Mappings check
    res_intents = client.get("/api/v1/ai/router/intents")
    assert res_intents.status_code == status.HTTP_403_FORBIDDEN

    # 2. Classifier check
    res_classify = client.post("/api/v1/ai/router/classify", json={"query": "test"})
    assert res_classify.status_code == status.HTTP_403_FORBIDDEN

    # 3. Test run pipeline
    res_test = client.post("/api/v1/ai/router/test", json={"query": "test"})
    assert res_test.status_code == status.HTTP_403_FORBIDDEN

    # 4. Stats check
    res_stats = client.get("/api/v1/ai/router/statistics")
    assert res_stats.status_code == status.HTTP_403_FORBIDDEN


def test_router_intents_success(client, mocks, admin_user):
    """Confirm admin can fetch intents mappings configuration successfully"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    
    response = client.get("/api/v1/ai/router/intents")
    assert response.status_code == 200
    
    data = response.json()
    assert "supported_intents" in data
    assert "registered_agents" in data
    assert "routing_rules" in data
    assert data["registered_agents"]["MEDICAL_QUESTION"] == "MedicalKnowledgeAgent"


def test_router_classify_success(client, mocks, admin_user):
    """Confirm admin can classify prompt queries directly"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    
    payload = {"query": "What are the side effects of aspirin and ibuprofen drug?"}
    
    response = client.post("/api/v1/ai/router/classify", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["detected_intent"] == "DRUG_INTERACTION"
    assert data["selected_agent"] == "DrugInteractionAgent"
    assert data["confidence"] > 0.0
    assert "matched_rules" in data


def test_router_statistics_success(client, mocks, admin_user):
    """Confirm admin can fetch router statistics metrics successfully"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    
    get_router_telemetry().reset()
    
    response = client.get("/api/v1/ai/router/statistics")
    assert response.status_code == 200
    
    data = response.json()
    assert data["total_routed_requests"] == 0
    assert data["average_routing_latency_ms"] == 0.0
    assert data["fallback_percentage"] == 0.0


def test_router_pipeline_test_success(client, mocks, admin_user):
    """Confirm admin can run a complete query state-graph test run routing"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    
    payload = {
        "query": "I have a terrible migraine pain and a cough fever symptoms",
        "debug_mode": True
    }
    
    response = client.post("/api/v1/ai/router/test", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "graph_trace" in data
    # Graph execution must include start, initialize, router, and finish nodes
    assert "__start__" in data["graph_trace"]
    assert "initialize_state" in data["graph_trace"]
    assert "router_agent" in data["graph_trace"]
    assert "__finish__" in data["graph_trace"]
    
    assert data["detected_intent"] == "SYMPTOM_ANALYSIS"
    assert data["selected_agent"] == "SymptomAgent"
    assert "routing_trace" in data
    assert data["latency_ms"] > 0.0
