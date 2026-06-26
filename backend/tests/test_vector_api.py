"""
Nura - Vector API Integration Tests
Tests route connectivity, admin role verification, collections inspection, and semantic verification test flow.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.core.dependencies import (
    get_current_user,
    get_vector_service,
    get_vector_collection_service,
    get_embedding_service
)
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


def test_vector_health_endpoint_admin_only(client, admin_user):
    """Verify that vector health is accessible to admins and returns formatted statistics"""
    mock_vector = MagicMock()
    mock_vector.health = AsyncMock(return_value={
        "status": "healthy",
        "connected": True,
        "latency": 15.4
    })
    
    mock_col = MagicMock()
    mock_col.get_collection_stats = AsyncMock(return_value={
        "name": "patient_reports",
        "status": "green",
        "vector_count": 50,
        "dimensions": 384,
        "distance": "COSINE",
        "storage_bytes": 1024
    })
    
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_vector_service] = lambda: mock_vector
    app.dependency_overrides[get_vector_collection_service] = lambda: mock_col
    
    response = client.get("/api/v1/ai/vector/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["connected"] is True
    assert len(data["collections"]) == 5
    assert data["collections"][0]["name"] == "patient_reports"
    assert data["collections"][0]["status"] == "green"


def test_vector_health_endpoint_patient_forbidden(client, patient_user):
    """Verify that patient role is forbidden from checking vector health details"""
    app.dependency_overrides[get_current_user] = lambda: patient_user
    
    response = client.get("/api/v1/ai/vector/health")
    assert response.status_code == 403


def test_vector_collections_endpoint(client, admin_user):
    """Verify that vector collections retrieval returns config specs"""
    mock_col = MagicMock()
    mock_col.get_collection_stats = AsyncMock(return_value={
        "name": "medical_knowledge",
        "status": "green",
        "vector_count": 200,
        "dimensions": 384,
        "distance": "COSINE",
        "storage_bytes": 2048
    })
    
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_vector_collection_service] = lambda: mock_col
    
    response = client.get("/api/v1/ai/vector/collections")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 5
    assert data[1]["name"] == "medical_knowledge"
    assert data[1]["vector_count"] == 200
    assert data[1]["dimensions"] == 384


def test_vector_test_endpoint_flow(client, admin_user):
    """Verify that the test pipeline endpoint executes the embed-upsert-search-delete cycle"""
    mock_embedding = MagicMock()
    mock_embedding.embed = AsyncMock(return_value=[0.1] * 384)
    mock_embedding.settings.EMBEDDING_MODEL = "bge-small"
    mock_embedding.settings.EMBEDDING_VERSION = "v1"
    
    mock_vector = MagicMock()
    mock_vector.upsert = AsyncMock(return_value=True)
    mock_vector.search = AsyncMock(return_value=[
        {"id": "test-uuid", "score": 0.99, "payload": {"source_id": "vector_playground_test"}}
    ])
    mock_vector.delete = AsyncMock(return_value=True)
    
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_embedding_service] = lambda: mock_embedding
    app.dependency_overrides[get_vector_service] = lambda: mock_vector
    
    payload = {
        "collection": "medical_knowledge",
        "text": "Hypertension symptoms and medication treatment"
    }
    
    response = client.post("/api/v1/ai/vector/test", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "latency" in data
    assert len(data["search_results"]) == 1
    assert data["search_results"][0]["id"] == "test-uuid"
    assert data["search_results"][0]["score"] == 0.99
    assert data["similarity_scores"] == [0.99]
    
    # Assert CRUD steps were executed
    mock_vector.upsert.assert_called_once()
    mock_vector.search.assert_called_once()
    mock_vector.delete.assert_called_once()
