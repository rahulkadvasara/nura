import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app
from app.models import UserRole, UserInDB
from app.core.dependencies import get_current_user
from app.services.drug_cache.drug_cache_service import DrugCacheService
from app.services.drug_background.scheduler import WorkerScheduler
from app.services.drug_background.queue_manager import DrugQueueManager
from app.services.drug_background.telemetry import DrugBackgroundTelemetry

@pytest.fixture
def mock_admin():
    from datetime import datetime, timezone
    return UserInDB(
        id="admin-123",
        email="admin@nura.com",
        password_hash="...",
        full_name="System Admin",
        role=UserRole.ADMIN,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

@pytest.fixture
def client(mock_admin):
    # Override current user to act as admin
    app.dependency_overrides[get_current_user] = lambda: mock_admin
    
    # Reset singletons to avoid "bound to a different event loop" errors in pytest
    import app.core.dependencies as deps
    deps._event_queue_instance = None
    deps._memory_sync_service_instance = None
    deps._drug_queue_manager_instance = None
    deps._drug_worker_scheduler_instance = None
    
    import app.services.drug_background.scheduler as sched
    sched._drug_worker_scheduler_instance = None
    
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_drug_system_health_endpoint(client):
    mock_ping = AsyncMock()
    
    with patch("app.db.mongodb.get_database") as mock_db_getter:
        mock_db = MagicMock()
        mock_db.command = mock_ping
        mock_db_getter.return_value = mock_db
        
        response = client.get("/api/v1/ai/drug/system/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "mongodb" in data["data"]
        assert "cache" in data["data"]
        assert "workers" in data["data"]
        assert "ai" in data["data"]
        assert "queue_depth" in data["data"]
        assert data["data"]["mongodb"] == "healthy"

def test_drug_system_cache_endpoint(client):
    response = client.get("/api/v1/ai/drug/system/cache")
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert "lookup_cache" in data["data"]
    assert "interaction_cache" in data["data"]
    assert "explanation_cache" in data["data"]
    assert "total_invalidations" in data["data"]

def test_drug_system_workers_endpoint(client):
    response = client.get("/api/v1/ai/drug/system/workers")
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert "total_workers" in data["data"]
    assert "active_workers" in data["data"]
    assert "idle_workers" in data["data"]
    assert "workers" in data["data"]
    assert "active_jobs" in data["data"]

def test_drug_system_statistics_endpoint(client):
    response = client.get("/api/v1/ai/drug/system/statistics")
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert "core" in data["data"]
    assert "background" in data["data"]
    assert "total_lookups" in data["data"]["core"]
    assert "ai_cost" in data["data"]["core"]
