"""
Nura - AI API Integration Tests
Tests route connectivity, public access constraints on /health, and authorization controls on /test.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.core.dependencies import get_current_user, get_ai_service, get_groq_service
from app.models.user import UserInDB, UserRole, AuthProvider
from app.services.ai_service import AIServiceResponse


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


def test_ai_health_endpoint_public(client):
    """Verify that the AI health check endpoint does not require authentication and returns correctly"""
    mock_groq_service = MagicMock()
    mock_groq_service.health_check = AsyncMock(return_value={
        "reachable": True,
        "model": "llama-3.3-70b-versatile",
        "latency_ms": 115.4,
        "status": "healthy",
        "timestamp": "2026-06-26T12:00:00Z"
    })
    
    app.dependency_overrides[get_groq_service] = lambda: mock_groq_service
    
    response = client.get("/api/v1/ai/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["reachable"] is True
    assert data["status"] == "healthy"
    assert data["model"] == "llama-3.3-70b-versatile"
    assert data["latency_ms"] == 115.4


def test_ai_test_endpoint_admin_authorized(client, admin_user):
    """Verify that administrators can access the playground testing router"""
    mock_ai_service = MagicMock()
    mock_response = AIServiceResponse(
        response="Mock testing playground response content",
        model="llama-3.3-70b-versatile",
        prompt_tokens=20,
        completion_tokens=40,
        total_tokens=60,
        latency_ms=180.0,
        finish_reason="stop",
        estimated_cost=0.0000434
    )
    mock_ai_service.generate = AsyncMock(return_value=mock_response)
    
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_ai_service] = lambda: mock_ai_service
    
    response = client.post("/api/v1/ai/test", json={"prompt": "Test query string"})
    assert response.status_code == 200
    
    data = response.json()
    assert data["response"] == "Mock testing playground response content"
    assert data["model"] == "llama-3.3-70b-versatile"
    assert data["token_usage"]["prompt_tokens"] == 20
    assert data["token_usage"]["completion_tokens"] == 40
    assert data["token_usage"]["total_tokens"] == 60
    assert data["latency"] == 180.0
    assert data["finish_reason"] == "stop"


def test_ai_test_endpoint_patient_forbidden(client, patient_user):
    """Verify that patients are forbidden from executing custom direct prompts"""
    app.dependency_overrides[get_current_user] = lambda: patient_user
    
    response = client.post("/api/v1/ai/test", json={"prompt": "Forbidden query string"})
    assert response.status_code == 403
