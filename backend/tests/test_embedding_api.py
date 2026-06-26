"""
Nura - Embedding API Integration Tests
Tests route connectivity, public access constraints on /embeddings/health, and role checks on /embeddings/test.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.core.dependencies import get_current_user, get_embedding_service
from app.models.user import UserInDB, UserRole, AuthProvider


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


def test_embedding_health_endpoint(client):
    """Verify that the embedding health check endpoint does not require authentication and returns correctly"""
    mock_service = MagicMock()
    mock_service.health_check = AsyncMock(return_value={
        "provider": "local",
        "model": "dummy-model",
        "dimensions": 384,
        "latency": 35.8,
        "status": "healthy"
    })
    
    app.dependency_overrides[get_embedding_service] = lambda: mock_service
    
    response = client.get("/api/v1/ai/embeddings/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["dimensions"] == 384
    assert data["provider"] == "local"
    assert data["latency"] == 35.8


def test_embedding_test_endpoint_admin_authorized(client, admin_user):
    """Verify that administrators can access the embedding verification test endpoint"""
    mock_service = MagicMock()
    mock_service.embed = AsyncMock(return_value=[0.2] * 384)
    mock_service.settings = MagicMock()
    mock_service.settings.EMBEDDING_MODEL = "dummy-model"
    mock_service.settings.EMBEDDING_VERSION = "v1"
    
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_embedding_service] = lambda: mock_service
    
    response = client.post("/api/v1/ai/embeddings/test", json={"text": "hello playground"})
    assert response.status_code == 200
    
    data = response.json()
    assert data["dimensions"] == 384
    assert len(data["vector_preview"]) == 5
    assert data["vector_preview"] == [0.2] * 5
    assert "metadata" in data
    assert data["metadata"]["document_type"] == "admin_test"


def test_embedding_test_endpoint_patient_forbidden(client, patient_user):
    """Verify that patients are forbidden from executing custom direct embedding tests"""
    app.dependency_overrides[get_current_user] = lambda: patient_user
    
    response = client.post("/api/v1/ai/embeddings/test", json={"text": "hello playground"})
    assert response.status_code == 403
