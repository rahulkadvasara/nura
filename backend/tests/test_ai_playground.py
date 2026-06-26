"""
Nura - AI Playground API Endpoint Integration Tests
Verifies playground route authorizations, parameter passing, and health check aggregate endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.core.dependencies import get_current_user, get_ai_orchestrator
from app.models.user import UserInDB, UserRole, AuthProvider
from app.schemas.ai import AIPlaygroundChatResponse, AIExecutionSession


@pytest.fixture
def client():
    """Build temporary TestClient for endpoint test invocations"""
    app.dependency_overrides.clear()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user():
    """Mock Administrator User database record"""
    return UserInDB(
        id="507f1f77bcf86cd799439011",
        email="admin@example.com",
        password_hash="hashed_admin",
        full_name="Admin Administrator",
        role=UserRole.ADMIN,
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True
    )


@pytest.fixture
def patient_user():
    """Mock Standard Patient User database record"""
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


def test_playground_health_endpoint_admin_authorized(client, admin_user):
    """Verify that administrators can access the consolidated AI playground health checklist"""
    mock_orchestrator = MagicMock()
    mock_orchestrator.health_check = AsyncMock(return_value={
        "groq": {"reachable": True, "model": "llama-3.3-70b-versatile", "latency_ms": 95},
        "embedding": {"status": "healthy", "provider": "local", "model": "mini", "dimensions": 384, "latency": 2},
        "vector": {"connected": True, "status": "healthy", "collections": []},
        "prompt_registry": {"status": "healthy", "error": None, "version": "1.0.0", "templates_count": 7},
        "context_builder": {"status": "healthy", "error": None}
    })
    
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_ai_orchestrator] = lambda: mock_orchestrator
    
    response = client.get("/api/v1/ai/playground/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["groq"]["reachable"] is True
    assert data["embedding"]["status"] == "healthy"
    assert data["vector"]["connected"] is True
    assert data["prompt_registry"]["templates_count"] == 7
    assert data["context_builder"]["status"] == "healthy"


def test_playground_health_endpoint_patient_forbidden(client, patient_user):
    """Verify that patient accounts cannot access integrated health check aggregates"""
    app.dependency_overrides[get_current_user] = lambda: patient_user
    
    response = client.get("/api/v1/ai/playground/health")
    assert response.status_code == 403


def test_playground_chat_endpoint_admin_authorized(client, admin_user):
    """Verify that administrators can run integrated chat playground sessions"""
    mock_orchestrator = MagicMock()
    
    mock_session = AIExecutionSession(
        request_id="trace_session_123",
        user_id=admin_user.id,
        patient_id="patient_555",
        model="llama-3.3-70b-versatile",
        start_time="2026-06-26T12:00:00Z",
        end_time="2026-06-26T12:00:01Z",
        duration=1000.0,
        tokens=250,
        cost=0.00018,
        status="success"
    )
    
    mock_response = AIPlaygroundChatResponse(
        response="Integrated chat output response.",
        execution_session=mock_session,
        prompt_template="Medical AI system prompt with context and user query.",
        patient_context_sections=["patient_profile", "medical_summary", "current_conditions"]
    )
    
    mock_orchestrator.execute_chat = AsyncMock(return_value=mock_response)
    
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_ai_orchestrator] = lambda: mock_orchestrator
    
    request_payload = {
        "prompt": "Test medical advice request",
        "patient_id": "patient_555",
        "model": "llama-3.3-70b-versatile",
        "temperature": 0.8,
        "max_tokens": 1000
    }
    
    response = client.post("/api/v1/ai/playground/chat", json=request_payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["response"] == "Integrated chat output response."
    assert data["execution_session"]["request_id"] == "trace_session_123"
    assert data["execution_session"]["cost"] == 0.00018
    assert data["prompt_template"] == "Medical AI system prompt with context and user query."
    assert "current_conditions" in data["patient_context_sections"]


def test_playground_chat_endpoint_patient_forbidden(client, patient_user):
    """Verify standard patients are rejected from invoking AI chat pipeline endpoint"""
    app.dependency_overrides[get_current_user] = lambda: patient_user
    
    request_payload = {
        "prompt": "Attempt forbidden query"
    }
    
    response = client.post("/api/v1/ai/playground/chat", json=request_payload)
    assert response.status_code == 403
