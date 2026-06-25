import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.core.dependencies import (
    get_current_user,
    get_audit_log_service,
    get_agent_log_service,
)
from app.models.user import UserInDB, UserRole, AuthProvider
from app.models.observability import AuditLogInDB, AgentLogInDB, AgentLogStatus

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
        "/api/v1/admin/logs/audit",
        "/api/v1/admin/logs/audit/some_id",
        "/api/v1/admin/logs/agents",
        "/api/v1/admin/logs/agents/some_id",
        "/api/v1/admin/logs/authentication",
    ]:
        response = client.get(path)
        assert response.status_code == 403
        assert "permitted" in response.json()["message"].lower()

def test_audit_logs_retrieval_and_filters(client, admin_user):
    app.dependency_overrides[get_current_user] = lambda: admin_user

    mock_audit_svc = AsyncMock()
    now = utc_now()
    dummy_log = AuditLogInDB(
        id="log_123",
        user_id="user_id_123",
        action="DOCTOR_APPROVED",
        resource_type="doctor_profile",
        resource_id="doc_profile_id_123",
        created_at=now
    )
    mock_audit_svc.get_audit_logs_paginated.return_value = ([dummy_log], 1)
    # Mock to_response mapping
    from app.schemas.observability import AuditLogResponse
    mock_audit_svc.to_response = MagicMock(return_value=AuditLogResponse(
        id="log_123",
        user_id="user_id_123",
        action="DOCTOR_APPROVED",
        resource_type="doctor_profile",
        resource_id="doc_profile_id_123",
        created_at=now
    ))
    app.dependency_overrides[get_audit_log_service] = lambda: mock_audit_svc

    response = client.get(
        "/api/v1/admin/logs/audit?limit=10&skip=0&search=DOCTOR&action=DOCTOR_APPROVED&resource_type=doctor_profile&start_date=2026-06-01&end_date=2026-06-30&user_id=user_id_123"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total"] == 1
    assert data["data"]["logs"][0]["id"] == "log_123"

    mock_audit_svc.get_audit_logs_paginated.assert_called_once_with(
        limit=10,
        skip=0,
        search="DOCTOR",
        user_id="user_id_123",
        role=None,
        action="DOCTOR_APPROVED",
        resource_type="doctor_profile",
        start_date="2026-06-01",
        end_date="2026-06-30"
    )

def test_audit_logs_role_filter(client, admin_user):
    app.dependency_overrides[get_current_user] = lambda: admin_user

    mock_audit_svc = AsyncMock()
    mock_audit_svc.get_audit_logs_paginated.return_value = ([], 0)
    app.dependency_overrides[get_audit_log_service] = lambda: mock_audit_svc

    response = client.get("/api/v1/admin/logs/audit?role=doctor")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total"] == 0

    mock_audit_svc.get_audit_logs_paginated.assert_called_once_with(
        limit=50,
        skip=0,
        search=None,
        user_id=None,
        role="doctor",
        action=None,
        resource_type=None,
        start_date=None,
        end_date=None
    )

def test_auth_logs_filtering(client, admin_user):
    app.dependency_overrides[get_current_user] = lambda: admin_user

    mock_audit_svc = AsyncMock()
    now = utc_now()
    dummy_log = AuditLogInDB(
        id="log_auth",
        user_id=admin_user.id,
        action="ADMIN_LOGIN",
        resource_type="admin",
        resource_id=admin_user.id,
        created_at=now
    )
    mock_audit_svc.get_auth_logs_paginated.return_value = ([dummy_log], 1)
    from app.schemas.observability import AuditLogResponse
    mock_audit_svc.to_response = MagicMock(return_value=AuditLogResponse(
        id="log_auth",
        user_id=admin_user.id,
        action="ADMIN_LOGIN",
        resource_type="admin",
        resource_id=admin_user.id,
        created_at=now
    ))
    app.dependency_overrides[get_audit_log_service] = lambda: mock_audit_svc

    response = client.get("/api/v1/admin/logs/authentication?search=login&start_date=2026-06-20&end_date=2026-06-25")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total"] == 1
    assert data["data"]["logs"][0]["action"] == "ADMIN_LOGIN"

    mock_audit_svc.get_auth_logs_paginated.assert_called_once_with(
        limit=50,
        skip=0,
        search="login",
        start_date="2026-06-20",
        end_date="2026-06-25"
    )

def test_agent_logs_retrieval(client, admin_user):
    app.dependency_overrides[get_current_user] = lambda: admin_user

    mock_agent_svc = AsyncMock()
    now = utc_now()
    dummy_log = AgentLogInDB(
        id="log_agent_1",
        agent_name="router_agent",
        workflow_id="wf_1",
        session_id="session_1",
        status=AgentLogStatus.COMPLETED,
        latency_ms=150.0,
        created_at=now
    )
    mock_agent_svc.get_agent_logs_paginated.return_value = ([dummy_log], 1)
    from app.schemas.observability import AgentLogResponse
    mock_agent_svc.to_response = MagicMock(return_value=AgentLogResponse(
        id="log_agent_1",
        agent_name="router_agent",
        workflow_id="wf_1",
        session_id="session_1",
        input_payload={},
        output_payload={},
        status=AgentLogStatus.COMPLETED,
        latency_ms=150.0,
        token_usage={},
        created_at=now
    ))
    app.dependency_overrides[get_agent_log_service] = lambda: mock_agent_svc

    response = client.get(
        "/api/v1/admin/logs/agents?agent=router_agent&status_filter=completed&session=session_1&start_date=2026-06-01&end_date=2026-06-30&limit=5&skip=2"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total"] == 1
    assert data["data"]["logs"][0]["agent_name"] == "router_agent"

    mock_agent_svc.get_agent_logs_paginated.assert_called_once_with(
        limit=5,
        skip=2,
        agent="router_agent",
        status="completed",
        session="session_1",
        start_date="2026-06-01",
        end_date="2026-06-30"
    )

def test_log_detail_not_found(client, admin_user):
    app.dependency_overrides[get_current_user] = lambda: admin_user

    mock_audit_svc = AsyncMock()
    mock_audit_svc.get_log_by_id.return_value = None
    app.dependency_overrides[get_audit_log_service] = lambda: mock_audit_svc

    mock_agent_svc = AsyncMock()
    mock_agent_svc.get_log_by_id.return_value = None
    app.dependency_overrides[get_agent_log_service] = lambda: mock_agent_svc

    response_audit = client.get("/api/v1/admin/logs/audit/missing_id")
    assert response_audit.status_code == 404
    assert "not found" in response_audit.json()["message"].lower()

    response_agent = client.get("/api/v1/admin/logs/agents/missing_id")
    assert response_agent.status_code == 404
    assert "not found" in response_agent.json()["message"].lower()
