"""
Nura - Observability and Audit Services Tests
Unit tests for AgentLogService and AuditLogService using mocked repositories.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from bson import ObjectId

from app.models.observability import (
    AgentLogInDB,
    AgentLogStatus,
    AuditLogInDB,
)
from app.models.user import UserInDB, UserRole, AuthProvider
from app.schemas.observability import (
    AgentLogCreateSchema,
    AgentLogUpdateSchema,
    AgentLogResponse,
    AuditLogCreateSchema,
    AuditLogResponse,
)
from app.services.agent_log_service import AgentLogService
from app.services.audit_log_service import AuditLogService


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.fixture
def sample_user():
    return UserInDB(
        id="507f1f77bcf86cd799439001",
        role=UserRole.PATIENT,
        email="patient@example.com",
        password_hash="hashed_pw",
        full_name="Patient Name",
        phone="1234567890",
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True,
        created_at=utc_now(),
        updated_at=utc_now(),
    )


@pytest.fixture
def sample_agent_log():
    return AgentLogInDB(
        id="507f1f77bcf86cd799439080",
        agent_name="router_agent",
        workflow_id="wf_123",
        session_id=None,
        patient_id=None,
        user_id=None,
        input_payload={"q": "fever"},
        output_payload={"ans": "viral"},
        status=AgentLogStatus.COMPLETED,
        latency_ms=100.0,
        token_usage={},
        error_message=None,
        created_at=utc_now(),
    )


@pytest.fixture
def sample_audit_log():
    return AuditLogInDB(
        id="507f1f77bcf86cd799439090",
        user_id="507f1f77bcf86cd799439001",
        action="profile_updated",
        resource_type="user",
        resource_id="507f1f77bcf86cd799439001",
        old_value=None,
        new_value=None,
        ip_address="127.0.0.1",
        user_agent="Firefox",
        created_at=utc_now(),
    )


class TestAgentLogService:
    @pytest.mark.asyncio
    async def test_create_log_success(self):
        log_repo = AsyncMock()
        log_repo.collection = MagicMock()
        log_repo.collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439080"))
        )
        log_repo.collection.find_one = AsyncMock(return_value={
            "_id": ObjectId("507f1f77bcf86cd799439080"),
            "agent_name": "router_agent",
            "workflow_id": "wf_123",
            "session_id": None,
            "patient_id": None,
            "user_id": None,
            "input_payload": {"q": "fever"},
            "output_payload": {"ans": "viral"},
            "status": "completed",
            "latency_ms": 100.0,
            "token_usage": {},
            "error_message": None,
            "created_at": utc_now(),
        })

        service = AgentLogService(log_repo)
        schema = AgentLogCreateSchema(
            agent_name="router_agent",
            workflow_id="wf_123",
            input_payload={"q": "fever"},
            output_payload={"ans": "viral"},
            status=AgentLogStatus.COMPLETED,
            latency_ms=100.0,
        )

        result = await service.create_log(schema)
        assert isinstance(result, AgentLogInDB)
        assert result.id == "507f1f77bcf86cd799439080"
        assert result.agent_name == "router_agent"

    @pytest.mark.asyncio
    async def test_get_log_by_id(self, sample_agent_log):
        log_repo = AsyncMock()
        log_repo.get = AsyncMock(return_value=sample_agent_log)
        service = AgentLogService(log_repo)

        result = await service.get_log_by_id(sample_agent_log.id)
        assert result == sample_agent_log
        log_repo.get.assert_called_once_with(sample_agent_log.id)

    @pytest.mark.asyncio
    async def test_update_log(self, sample_agent_log):
        log_repo = AsyncMock()
        log_repo.update = AsyncMock(return_value=sample_agent_log)
        service = AgentLogService(log_repo)

        schema = AgentLogUpdateSchema(status=AgentLogStatus.FAILED, error_message="Error")
        result = await service.update_log(sample_agent_log.id, schema)
        assert result == sample_agent_log
        log_repo.update.assert_called_once()

    def test_to_response(self, sample_agent_log):
        log_repo = AsyncMock()
        service = AgentLogService(log_repo)
        resp = service.to_response(sample_agent_log)
        assert isinstance(resp, AgentLogResponse)
        assert resp.id == sample_agent_log.id
        assert resp.agent_name == sample_agent_log.agent_name


class TestAuditLogService:
    @pytest.mark.asyncio
    async def test_create_audit_success(self, sample_user):
        audit_repo = AsyncMock()
        audit_repo.collection = MagicMock()
        audit_repo.collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439090"))
        )
        audit_repo.collection.find_one = AsyncMock(return_value={
            "_id": ObjectId("507f1f77bcf86cd799439090"),
            "user_id": sample_user.id,
            "action": "profile_updated",
            "resource_type": "user",
            "resource_id": sample_user.id,
            "old_value": None,
            "new_value": None,
            "ip_address": "127.0.0.1",
            "user_agent": "Firefox",
            "created_at": utc_now(),
        })

        user_repo = AsyncMock()
        user_repo.get = AsyncMock(return_value=sample_user)

        service = AuditLogService(audit_repo, user_repo)
        schema = AuditLogCreateSchema(
            user_id=sample_user.id,
            action="profile_updated",
            resource_type="user",
            resource_id=sample_user.id,
        )

        result = await service.create_log(schema)
        assert isinstance(result, AuditLogInDB)
        assert result.id == "507f1f77bcf86cd799439090"
        user_repo.get.assert_called_once_with(sample_user.id)

    @pytest.mark.asyncio
    async def test_create_audit_user_not_found(self):
        audit_repo = AsyncMock()
        user_repo = AsyncMock()
        user_repo.get = AsyncMock(return_value=None)

        service = AuditLogService(audit_repo, user_repo)
        schema = AuditLogCreateSchema(
            user_id="invalid_user",
            action="report_uploaded",
            resource_type="report",
        )

        with pytest.raises(ValueError, match="User with ID.*does not exist"):
            await service.create_log(schema)

    @pytest.mark.asyncio
    async def test_create_audit_no_user_provided(self):
        audit_repo = AsyncMock()
        audit_repo.collection = MagicMock()
        audit_repo.collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439090"))
        )
        audit_repo.collection.find_one = AsyncMock(return_value={
            "_id": ObjectId("507f1f77bcf86cd799439090"),
            "user_id": None,
            "action": "system_event",
            "resource_type": "system",
            "resource_id": None,
            "old_value": None,
            "new_value": None,
            "ip_address": "127.0.0.1",
            "user_agent": "Firefox",
            "created_at": utc_now(),
        })
        user_repo = AsyncMock()

        service = AuditLogService(audit_repo, user_repo)
        schema = AuditLogCreateSchema(
            action="system_event",
            resource_type="system",
        )

        result = await service.create_log(schema)
        assert result.user_id is None
        user_repo.get.assert_not_called()
