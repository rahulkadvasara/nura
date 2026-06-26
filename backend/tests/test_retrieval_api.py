"""
Nura - API integration tests for Retrieval routes
"""
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.core.dependencies import get_current_user, get_retrieval_service, get_auth_service
from app.models.user import UserInDB, UserRole, AuthProvider
from app.utils.ai import retrieval_metrics


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
        id="admin_123",
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
    """Mock Patient User record"""
    return UserInDB(
        id="patient_123",
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


@pytest.fixture
def mock_retrieval_service():
    service = AsyncMock()
    service.retrieve.return_value = {
        "results": [
            {
                "collection": "patient_reports",
                "id": "hit_1",
                "score": 0.85,
                "content": "Patient presents with symptoms of asthma.",
                "metadata": {"content_hash": "hash_a", "document_type": "REPORT"},
                "document_type": "REPORT",
                "patient_id": "pat_1",
                "report_id": "rep_1",
                "citations": {"document_id": "doc_1", "page_number": 2}
            }
        ],
        "retrieval_time": 12.5,
        "collections_queried": ["patient_reports"],
        "chunks_found": 1,
        "duplicates_removed": 0
    }
    service.retrieve_multiple.return_value = {
        "results": [],
        "retrieval_time": 5.0,
        "collections_queried": ["patient_reports", "medical_knowledge"],
        "chunks_found": 0,
        "duplicates_removed": 0
    }
    return service


def test_retrieve_endpoint_unauthorized(client, mocks, patient_user):
    """Confirm patients are rejected with 403 on retrieve endpoints"""
    app.dependency_overrides[get_current_user] = lambda: patient_user
    
    response = client.post(
        "/api/v1/ai/retrieve/single",
        json={"query": "asthma", "collections": ["REPORT"]}
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_retrieve_endpoint_authorized(client, mocks, admin_user, mock_retrieval_service):
    """Confirm admin can execute retrieval"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_retrieval_service] = lambda: mock_retrieval_service
    
    response = client.post(
        "/api/v1/ai/retrieve/single",
        json={"query": "asthma", "collection": "patient_reports", "collections": ["patient_reports"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 1
    assert data["results"][0]["id"] == "hit_1"
    assert data["results"][0]["score"] == 0.85
    assert data["results"][0]["content"] == "Patient presents with symptoms of asthma."
    mock_retrieval_service.retrieve.assert_called_once()


def test_retrieve_multi_endpoint_authorized(client, mocks, admin_user, mock_retrieval_service):
    """Confirm admin can execute multi-collection retrieval"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_retrieval_service] = lambda: mock_retrieval_service
    
    response = client.post(
        "/api/v1/ai/retrieve/multi",
        json={"query": "flu", "collections": ["patient_reports", "medical_knowledge"]}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert data["collections_queried"] == ["patient_reports", "medical_knowledge"]
    mock_retrieval_service.retrieve_multiple.assert_called_once()


def test_get_statistics_endpoint(client, mocks, admin_user):
    """Confirm stats endpoint returns correct metrics fields"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    
    retrieval_metrics.reset()
    # Record a search hit to verify metrics reporting accuracy
    retrieval_metrics.record_search(
        latency_ms=10.0,
        success=True,
        hits_count=2,
        avg_score=0.9,
        duplicates_removed=1,
        timeout=False
    )
    
    response = client.get("/api/v1/ai/retrieve/statistics/raw")
    
    assert response.status_code == 200
    data = response.json()
    assert data["searches_executed"] == 1
    assert data["failed_searches"] == 0
    assert data["avg_latency_ms"] == 10.0
    assert data["avg_score"] == 0.9
    assert data["duplicate_chunks_removed"] == 1
