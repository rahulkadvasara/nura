"""
Nura - Integration tests for RetrievalAgent and its endpoints
"""
import pytest
import time
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.core.dependencies import get_current_user, get_retrieval_agent, get_auth_service
from app.models.user import UserInDB, UserRole, AuthProvider
from app.agents.retrieval_agent import retrieval_cache
from app.utils.ai import retrieval_agent_metrics

@pytest.fixture
def client():
    app.dependency_overrides.clear()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def admin_user():
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
def mock_retrieval_agent():
    agent = AsyncMock()
    # Mocking standard response shape
    agent.run.return_value = MagicMock(
        success=True,
        response={
            "intent": "medical_question",
            "collections_used": ["medical_knowledge", "patient_reports"],
            "retrieved_chunks": [],
            "context": "Sample Assembled Context",
            "citations": {"1": {"collection": "medical_knowledge", "document_id": "doc_1"}},
            "metadata": {"intent_scores": {"medical_question": 10}, "token_budget": 4000},
            "latency": {"retrieval": 5.0, "ranking": 1.0, "context": 4.0, "total": 10.0},
            "scores": {},
            "cache_status": "miss"
        }
    )
    return agent

@pytest.fixture
def mocks():
    auth_svc = MagicMock()
    auth_svc.require_role = lambda u, r: None
    app.dependency_overrides[get_auth_service] = lambda: auth_svc
    return auth_svc

def test_retrieval_agent_cache_logic():
    """Verify in-memory TTL caching behaves correctly"""
    retrieval_cache.clear()
    
    # Test setting
    patient_id = "pat_123"
    query = "asthma symptoms"
    intent = "medical_question"
    result_data = {"test": "val", "cache_status": "miss"}
    
    retrieval_cache.set(patient_id, query, intent, result_data)
    
    # Test get hit
    cached = retrieval_cache.get(patient_id, query, intent)
    assert cached is not None
    assert cached["test"] == "val"
    
    # Test expire
    retrieval_cache.ttl = -1 # Force instant expire
    expired = retrieval_cache.get(patient_id, query, intent)
    assert expired is None
    
    # Reset cache settings
    retrieval_cache.ttl = 300
    retrieval_cache.clear()

def test_api_retrieve_agent_endpoint(client, mocks, admin_user, mock_retrieval_agent):
    """Test retrieval agent API execution"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_retrieval_agent] = lambda: mock_retrieval_agent
    
    response = client.post(
        "/api/v1/ai/retrieve",
        json={"query": "heart symptoms", "patient_id": "pat_abc"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "medical_question"
    assert data["context"] == "Sample Assembled Context"
    assert "citations" in data
    assert data["cache_status"] == "miss"
    mock_retrieval_agent.run.assert_called_once()

def test_api_retrieve_debug_endpoint(client, mocks, admin_user, mock_retrieval_agent):
    """Test debug retrieval agent API bypasses cache"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_retrieval_agent] = lambda: mock_retrieval_agent
    
    response = client.post(
        "/api/v1/ai/retrieve/debug",
        json={"query": "glucose report", "patient_id": "pat_xyz"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "medical_question"
    mock_retrieval_agent.run.assert_called_once()
    # Check that bypass_cache is passed in context metadata
    args, kwargs = mock_retrieval_agent.run.call_args
    context = args[1]
    assert context.metadata["bypass_cache"] is True

def test_api_retrieve_statistics(client, mocks, admin_user):
    """Test retrieval agent statistics endpoint"""
    app.dependency_overrides[get_current_user] = lambda: admin_user
    
    retrieval_agent_metrics.reset()
    retrieval_agent_metrics.record_execution(
        intent="medical_question",
        collections=["medical_knowledge"],
        cache_hit=False,
        retrieval_latency_ms=10.0,
        ranking_latency_ms=2.0,
        context_latency_ms=8.0,
        total_latency_ms=20.0,
        success=True
    )
    
    response = client.get("/api/v1/ai/retrieve/statistics")
    
    assert response.status_code == 200
    data = response.json()
    assert data["requests"] == 1
    assert data["cache_misses"] == 1
    assert data["avg_latency_ms"] == 20.0
    assert data["avg_retrieval_latency_ms"] == 10.0
    assert "medical_question" in data["intent_counts"]
