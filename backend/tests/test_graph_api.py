"""
Nura Backend - Graph API Integration Tests
Verifies RBAC rules and execution validation response parameters of graph admin routes.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.core.dependencies import get_current_user, get_auth_service
from app.models.user import UserInDB, UserRole, AuthProvider
from app.graph.telemetry import get_graph_telemetry


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
    """Mock AuthService to bypass real db query during dependency injection checks"""
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


def test_graph_endpoints_patient_forbidden(client, mocks, patient_user):
    """Confirm patient users get 403 on Graph administrative routes"""
    app.dependency_overrides[get_current_user] = lambda: patient_user
    
    # 1. Health check
    res_health = client.get("/api/v1/ai/graph/health")
    assert res_health.status_code == status.HTTP_403_FORBIDDEN

    # 2. Nodes directory
    res_nodes = client.get("/api/v1/ai/graph/nodes")
    assert res_nodes.status_code == status.HTTP_403_FORBIDDEN

    # 3. Test execution
    res_test = client.post("/api/v1/ai/graph/test", json={"query": "test query"})
    assert res_test.status_code == status.HTTP_403_FORBIDDEN

    # 4. Stats metrics
    res_stats = client.get("/api/v1/ai/graph/statistics")
    assert res_stats.status_code == status.HTTP_403_FORBIDDEN


def test_graph_health_success(client, mocks, admin_user):
    """Confirm admins can fetch graph health status successfully"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    
    response = client.get("/api/v1/ai/graph/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["graph_compiled"] is True
    assert "registered_nodes" in data
    assert "registered_transitions" in data


def test_graph_nodes_success(client, mocks, admin_user):
    """Confirm admins can retrieve nodes list successfully"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    
    response = client.get("/api/v1/ai/graph/nodes")
    assert response.status_code == 200
    
    data = response.json()
    assert "nodes" in data
    assert len(data["nodes"]) > 0
    assert "__start__" in data["nodes"]
    assert "__finish__" in data["nodes"]


def test_graph_statistics_success(client, mocks, admin_user):
    """Confirm admins can fetch stats cumulative metrics successfully"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    
    # Reset telemetry tracker
    get_graph_telemetry().reset()
    
    response = client.get("/api/v1/ai/graph/statistics")
    assert response.status_code == 200
    
    data = response.json()
    assert data["total_executions"] == 0
    assert data["successful_executions"] == 0
    assert data["failed_executions"] == 0


def test_graph_test_run_success(client, mocks, admin_user):
    """Confirm admins can run mock workflow graph and retrieve trace timelines"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    
    payload = {
        "query": "Cholesterol analysis query text",
        "patient_id": "507f1f77bcf86cd799439012",
        "debug_mode": True,
        "metadata": {"caller": "integration_tester"}
    }
    
    response = client.post("/api/v1/ai/graph/test", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "trace" in data
    assert "__start__" in data["trace"]
    assert "initialize_state" in data["trace"]
    assert "router_placeholder" in data["trace"]
    assert "__finish__" in data["trace"]
    assert "timings" in data
    assert "overall" in data["timings"]
    assert data["state"]["query"] == payload["query"]
    assert data["state"]["patient_id"] == payload["patient_id"]
