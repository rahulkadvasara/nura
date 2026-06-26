"""
Nura - AI Context Assembly API Integration Tests
"""
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.core.dependencies import get_current_user, get_context_assembly_service, get_auth_service
from app.models.user import UserInDB, UserRole, AuthProvider
from app.utils.ai import context_assembly_metrics


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


def test_build_context_admin_only(client, mocks, patient_user):
    """Confirm patients are rejected with 403 on context building endpoint"""
    app.dependency_overrides[get_current_user] = lambda: patient_user
    
    response = client.post("/api/v1/ai/context/build", json={
        "query": "hypertension medications",
        "patient_id": "pat_123"
    })
    
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_build_context_successful(client, mocks, admin_user):
    """Confirm admin can successfully call context build"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    
    mock_assembly_service = MagicMock()
    mock_assembly_service.assemble = AsyncMock(return_value={
        "sections": {
            "PATIENT SUMMARY": "Patient summary text",
            "MEDICAL KNOWLEDGE": "Medical knowledge text"
        },
        "citations": {
            "Ref 1": {
                "source": "medical_knowledge",
                "collection": "medical_knowledge",
                "document_id": "doc_med_1",
                "chunk_id": "chunk_med_1",
                "page_number": 1,
                "score": 0.85
            }
        },
        "estimated_tokens": 100,
        "compression_ratio": 0.9,
        "assembly_time": 25.0,
        "metadata": {
            "query": "hypertension medications",
            "patient_id": "pat_123"
        }
    })
    app.dependency_overrides[get_context_assembly_service] = lambda: mock_assembly_service
    
    response = client.post("/api/v1/ai/context/build", json={
        "query": "hypertension medications",
        "patient_id": "pat_123",
        "token_budget": 4000
    })
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "sections" in data
    assert "citations" in data
    assert "estimated_tokens" in data
    assert data["estimated_tokens"] == 100
    assert "PATIENT SUMMARY" in data["sections"]
    assert "Ref 1" in data["citations"]


def test_get_context_statistics_admin_only(client, mocks, patient_user):
    """Confirm patients are rejected with 403 on statistics endpoint"""
    app.dependency_overrides[get_current_user] = lambda: patient_user
    
    response = client.get("/api/v1/ai/context/statistics")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_context_statistics_successful(client, mocks, admin_user):
    """Confirm admin can successfully retrieve context assembly statistics"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    
    context_assembly_metrics.reset()
    context_assembly_metrics.record_assembly(
        latency_ms=25.0,
        success=True,
        original_chunks=5,
        removed_chunks=2,
        compression_ratio=0.8,
        estimated_tokens=150,
        sections=["PATIENT SUMMARY", "MEDICAL KNOWLEDGE"]
    )
    
    response = client.get("/api/v1/ai/context/statistics")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["assemblies_executed"] == 1
    assert data["failed_assemblies"] == 0
    assert data["avg_latency_ms"] == 25.0
    assert data["avg_tokens_assembled"] == 150.0
    assert "PATIENT SUMMARY" in data["section_counts"]
