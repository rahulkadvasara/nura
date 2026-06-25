import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app
from app.core.dependencies import (
    get_current_user,
    get_system_monitor_service,
    get_maintenance_service,
    get_audit_log_service,
)
from app.models.user import UserInDB, UserRole, AuthProvider
from app.schemas.system import ServiceHealth, SystemInfoResponse, BackgroundJobResponse, BackgroundJobItem

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

@pytest.fixture
def client():
    app.dependency_overrides.clear()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def admin_user():
    now = utc_now()
    return UserInDB(
        id="507f1f77bcf86cd799439002",
        email="admin@example.com",
        password_hash="hashed_pw",
        full_name="Admin Name",
        role=UserRole.ADMIN,
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True,
        created_at=now,
        updated_at=now
    )

@pytest.fixture
def doctor_user():
    now = utc_now()
    return UserInDB(
        id="507f1f77bcf86cd799439003",
        email="doctor@example.com",
        password_hash="hashed_pw",
        full_name="Doctor Name",
        role=UserRole.DOCTOR,
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True,
        created_at=now,
        updated_at=now
    )

def test_unauthorized_endpoints(client, doctor_user):
    # Enforces that non-admins (e.g. doctors) receive 403 Forbidden
    app.dependency_overrides[get_current_user] = lambda: doctor_user

    for path in [
        "/api/v1/admin/system/health",
        "/api/v1/admin/system/jobs",
        "/api/v1/admin/system/info",
        "/api/v1/admin/system/maintenance/clear-sessions",
        "/api/v1/admin/system/maintenance/clear-otps",
        "/api/v1/admin/system/maintenance/archive-notifications",
        "/api/v1/admin/system/maintenance/archive-audit-logs",
    ]:
        if path.startswith("/api/v1/admin/system/maintenance"):
            response = client.post(path)
        else:
            response = client.get(path)
        assert response.status_code == 403
        assert "permitted" in response.json()["message"].lower()

def test_system_health_retrieval(client, admin_user):
    app.dependency_overrides[get_current_user] = lambda: admin_user

    mock_monitor_svc = AsyncMock()
    now = utc_now()
    dummy_health = [
        ServiceHealth(
            name="API Gateway",
            status="healthy",
            latency_ms=0,
            message="Operational",
            last_checked=now
        ),
        ServiceHealth(
            name="MongoDB",
            status="healthy",
            latency_ms=5,
            message="Connected successfully",
            last_checked=now
        )
    ]
    mock_monitor_svc.check_health.return_value = dummy_health
    app.dependency_overrides[get_system_monitor_service] = lambda: mock_monitor_svc

    response = client.get("/api/v1/admin/system/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]["services"]) == 2
    assert data["data"]["services"][0]["name"] == "API Gateway"
    assert data["data"]["services"][1]["status"] == "healthy"

def test_system_info_uptime(client, admin_user):
    app.dependency_overrides[get_current_user] = lambda: admin_user

    mock_monitor_svc = MagicMock()
    now = utc_now()
    dummy_info = SystemInfoResponse(
        version="1.0.0",
        environment="development",
        startup_time=now,
        uptime_seconds=3600.0
    )
    mock_monitor_svc.get_system_info.return_value = dummy_info
    app.dependency_overrides[get_system_monitor_service] = lambda: mock_monitor_svc

    response = client.get("/api/v1/admin/system/info")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["version"] == "1.0.0"
    assert data["data"]["uptime_seconds"] == 3600.0

def test_background_jobs_metrics(client, admin_user):
    app.dependency_overrides[get_current_user] = lambda: admin_user

    mock_monitor_svc = AsyncMock()
    now = utc_now()
    job_item = BackgroundJobItem(
        status="active",
        running=1,
        completed=10,
        failed=0,
        queued=5,
        last_execution=now,
        next_execution=now
    )
    dummy_jobs = BackgroundJobResponse(
        reminder_jobs=job_item,
        notification_jobs=BackgroundJobItem(
            status="Not configured", running=0, completed=0, failed=0, queued=0, last_execution=None, next_execution=None
        ),
        ai_jobs=BackgroundJobItem(
            status="Not configured", running=0, completed=0, failed=0, queued=0, last_execution=None, next_execution=None
        ),
        failed_jobs=BackgroundJobItem(
            status="Not configured", running=0, completed=0, failed=0, queued=0, last_execution=None, next_execution=None
        )
    )
    mock_monitor_svc.get_background_jobs.return_value = dummy_jobs
    app.dependency_overrides[get_system_monitor_service] = lambda: mock_monitor_svc

    response = client.get("/api/v1/admin/system/jobs")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["reminder_jobs"]["status"] == "active"
    assert data["data"]["ai_jobs"]["status"] == "Not configured"

def test_maintenance_clearups(client, admin_user):
    app.dependency_overrides[get_current_user] = lambda: admin_user

    mock_maintenance_svc = AsyncMock()
    mock_maintenance_svc.clear_expired_sessions.return_value = 5
    mock_maintenance_svc.clear_expired_otps.return_value = 12
    mock_maintenance_svc.archive_notifications.return_value = 25
    mock_maintenance_svc.archive_audit_logs.return_value = 50
    app.dependency_overrides[get_maintenance_service] = lambda: mock_maintenance_svc

    mock_audit_svc = AsyncMock()
    app.dependency_overrides[get_audit_log_service] = lambda: mock_audit_svc

    # 1. Clear sessions
    response = client.post("/api/v1/admin/system/maintenance/clear-sessions")
    assert response.status_code == 200
    assert response.json()["data"]["deleted_count"] == 5
    mock_audit_svc.create_log.assert_called()

    # 2. Clear OTPs
    mock_audit_svc.create_log.reset_mock()
    response = client.post("/api/v1/admin/system/maintenance/clear-otps")
    assert response.status_code == 200
    assert response.json()["data"]["deleted_count"] == 12
    mock_audit_svc.create_log.assert_called()

    # 3. Archive Notifications
    mock_audit_svc.create_log.reset_mock()
    response = client.post("/api/v1/admin/system/maintenance/archive-notifications?retention_days=15")
    assert response.status_code == 200
    assert response.json()["data"]["archived_count"] == 25
    mock_maintenance_svc.archive_notifications.assert_called_with(retention_days=15)
    mock_audit_svc.create_log.assert_called()

    # 4. Archive Audit Logs
    mock_audit_svc.create_log.reset_mock()
    response = client.post("/api/v1/admin/system/maintenance/archive-audit-logs?retention_days=60")
    assert response.status_code == 200
    assert response.json()["data"]["archived_count"] == 50
    mock_maintenance_svc.archive_audit_logs.assert_called_with(retention_days=60)
    mock_audit_svc.create_log.assert_called()
