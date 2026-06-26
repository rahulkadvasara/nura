"""
Nura - AI Document Indexing API Integration Tests
"""
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.core.dependencies import get_current_user, get_document_indexing_service, get_auth_service
from app.models.user import UserInDB, UserRole, AuthProvider


@pytest.fixture
def client():
    """Build temporary TestClient for endpoint test invokes"""
    app.dependency_overrides.clear()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user():
    """Mock Administrator User record"""
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
    """Mock Patient User record"""
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
    """Mock AuthService to bypass real database connection during RBAC verification"""
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


def test_index_document_admin_only(client, mocks, patient_user):
    """Confirm patients are rejected with 403 on indexing endpoints"""
    app.dependency_overrides[get_current_user] = lambda: patient_user
    
    response = client.post("/api/v1/ai/index", json={
        "document_id": "doc_123",
        "document_type": "REPORT",
        "content": "Patient records details content."
    })
    
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_index_document_successful(client, mocks, admin_user):
    """Confirm admin can successfully index a document"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    
    mock_indexing_service = MagicMock()
    mock_indexing_service.index_document = AsyncMock(return_value={
        "success": True,
        "document_id": "doc_123",
        "status": "indexed",
        "chunks_count": 2,
        "skipped_count": 0,
        "latency_ms": 45.2,
        "message": "Document successfully vectorized and indexed in Qdrant."
    })
    app.dependency_overrides[get_document_indexing_service] = lambda: mock_indexing_service
    
    response = client.post("/api/v1/ai/index", json={
        "document_id": "doc_123",
        "document_type": "REPORT",
        "content": "Patient blood pressure is high.",
        "chunking_strategy": "fixed",
        "chunk_size": 200,
        "overlap": 20
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "indexed"
    assert data["chunks_count"] == 2
    mock_indexing_service.index_document.assert_called_once()


def test_batch_index_documents(client, mocks, admin_user):
    """Confirm batch indexing endpoint maps lists and returns responses"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    
    mock_indexing_service = MagicMock()
    mock_indexing_service.index_documents = AsyncMock(return_value=[
        {
            "success": True,
            "document_id": "doc_a",
            "status": "indexed",
            "chunks_count": 1,
            "skipped_count": 0,
            "latency_ms": 20.0
        },
        {
            "success": True,
            "document_id": "doc_b",
            "status": "skipped",
            "chunks_count": 0,
            "skipped_count": 1,
            "latency_ms": 5.0,
            "message": "All chunks skipped"
        }
    ])
    app.dependency_overrides[get_document_indexing_service] = lambda: mock_indexing_service
    
    payload = {
        "documents": [
            {"document_id": "doc_a", "document_type": "REPORT", "content": "Text content A"},
            {"document_id": "doc_b", "document_type": "REPORT", "content": "Text content B"}
        ]
    }
    
    response = client.post("/api/v1/ai/batch-index", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 2
    assert data["results"][0]["document_id"] == "doc_a"
    assert data["results"][0]["status"] == "indexed"
    assert data["results"][1]["document_id"] == "doc_b"
    assert data["results"][1]["status"] == "skipped"


def test_reindex_document(client, mocks, admin_user):
    """Confirm reindexing executes reindex call"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    
    mock_indexing_service = MagicMock()
    mock_indexing_service.reindex_document = AsyncMock(return_value={
        "success": True,
        "document_id": "doc_123",
        "status": "indexed",
        "chunks_count": 1
    })
    app.dependency_overrides[get_document_indexing_service] = lambda: mock_indexing_service
    
    response = client.post("/api/v1/ai/reindex", json={
        "document_id": "doc_123",
        "document_type": "REPORT",
        "content": "New report text"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "indexed"


def test_delete_document(client, mocks, admin_user):
    """Confirm deleting single document deletes vectors"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    
    mock_indexing_service = MagicMock()
    mock_indexing_service.delete_document = AsyncMock(return_value=True)
    app.dependency_overrides[get_document_indexing_service] = lambda: mock_indexing_service
    
    response = client.delete("/api/v1/ai/document?document_id=doc_123&document_type=REPORT")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "successfully removed" in data["message"]
    mock_indexing_service.delete_document.assert_called_once_with("doc_123", "REPORT")


def test_delete_patient_documents(client, mocks, admin_user):
    """Confirm deleting patient documents works"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    
    mock_indexing_service = MagicMock()
    mock_indexing_service.delete_patient_documents = AsyncMock(return_value=True)
    app.dependency_overrides[get_document_indexing_service] = lambda: mock_indexing_service
    
    response = client.delete("/api/v1/ai/patient?patient_id=pat_123")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "reports deleted successfully" in data["message"]
    mock_indexing_service.delete_patient_documents.assert_called_once_with("pat_123")


def test_get_indexing_statistics(client, mocks, admin_user):
    """Confirm metrics are returned correctly"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    
    mock_indexing_service = MagicMock()
    mock_indexing_service.compute_statistics = MagicMock(return_value={
        "indexed_documents": 10,
        "indexed_chunks": 45,
        "duplicate_documents_skipped": 2,
        "avg_chunk_size": 250.5,
        "embedding_version": "v1",
        "index_version": 3,
        "schema_version": 2
    })
    app.dependency_overrides[get_document_indexing_service] = lambda: mock_indexing_service
    
    response = client.get("/api/v1/ai/index/statistics")
    
    assert response.status_code == 200
    data = response.json()
    assert data["indexed_documents"] == 10
    assert data["indexed_chunks"] == 45
    assert data["duplicate_documents_skipped"] == 2
    assert data["avg_chunk_size"] == 250.5
    assert data["embedding_version"] == "v1"
    assert data["index_version"] == 3
    assert data["schema_version"] == 2
    mock_indexing_service.compute_statistics.assert_called_once()
