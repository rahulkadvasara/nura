"""
Nura - Observability and Audit Repositories Tests
Unit tests for AgentLogRepository and AuditLogRepository using mocked MongoDB collections.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from bson import ObjectId

from app.models.observability import (
    AgentLogCreate,
    AgentLogUpdate,
    AgentLogInDB,
    AgentLogStatus,
    AuditLogCreate,
    AuditLogUpdate,
    AuditLogInDB,
)
from app.repositories.agent_log_repository import AgentLogRepository
from app.repositories.audit_log_repository import AuditLogRepository


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def make_agent_log_doc(
    log_id: str = "507f1f77bcf86cd799439080",
    agent_name: str = "router_agent",
    workflow_id: str = "wf_123",
) -> dict:
    now = utc_now()
    return {
        "_id": ObjectId(log_id),
        "agent_name": agent_name,
        "workflow_id": workflow_id,
        "session_id": None,
        "patient_id": None,
        "user_id": None,
        "input_payload": {},
        "output_payload": {},
        "status": "started",
        "latency_ms": 0.0,
        "token_usage": {},
        "error_message": None,
        "created_at": now,
    }


def make_audit_log_doc(
    log_id: str = "507f1f77bcf86cd799439090",
    user_id: str = "507f1f77bcf86cd799439001",
) -> dict:
    now = utc_now()
    return {
        "_id": ObjectId(log_id),
        "user_id": user_id,
        "action": "report_uploaded",
        "resource_type": "report",
        "resource_id": "report_123",
        "old_value": None,
        "new_value": None,
        "ip_address": "127.0.0.1",
        "user_agent": "Firefox",
        "created_at": now,
    }


def make_mock_collection(find_one_return=None, find_return=None, update_result=None):
    collection = MagicMock()
    collection.find_one = AsyncMock(return_value=find_one_return)

    insert_result = MagicMock()
    insert_result.inserted_id = ObjectId("507f1f77bcf86cd799439080")
    collection.insert_one = AsyncMock(return_value=insert_result)

    upd_result = MagicMock()
    upd_result.modified_count = 1 if update_result is None else update_result
    collection.update_one = AsyncMock(return_value=upd_result)

    del_result = MagicMock()
    del_result.deleted_count = 1
    collection.delete_one = AsyncMock(return_value=del_result)

    cursor = MagicMock()
    cursor.skip = MagicMock(return_value=cursor)
    cursor.limit = MagicMock(return_value=cursor)
    cursor.to_list = AsyncMock(return_value=find_return or [])
    collection.find = MagicMock(return_value=cursor)

    return collection


class TestAgentLogRepository:
    @pytest.mark.asyncio
    async def test_create_log(self):
        doc = make_agent_log_doc()
        collection = make_mock_collection(find_one_return=doc)
        repo = AgentLogRepository(collection)

        log_create = AgentLogCreate(
            agent_name="router_agent",
            workflow_id="wf_123",
        )
        result = await repo.create(log_create)
        assert isinstance(result, AgentLogInDB)
        assert result.agent_name == "router_agent"
        assert result.workflow_id == "wf_123"

    @pytest.mark.asyncio
    async def test_get_log_by_id(self):
        doc = make_agent_log_doc()
        collection = make_mock_collection(find_one_return=doc)
        repo = AgentLogRepository(collection)

        result = await repo.get_by_id("507f1f77bcf86cd799439080")
        assert result is not None
        assert result.id == "507f1f77bcf86cd799439080"

    @pytest.mark.asyncio
    async def test_get_by_agent(self):
        docs = [make_agent_log_doc()]
        collection = make_mock_collection(find_return=docs)
        repo = AgentLogRepository(collection)

        results = await repo.get_by_agent("router_agent")
        assert len(results) == 1
        assert results[0].agent_name == "router_agent"

    @pytest.mark.asyncio
    async def test_get_by_workflow(self):
        docs = [make_agent_log_doc()]
        collection = make_mock_collection(find_return=docs)
        repo = AgentLogRepository(collection)

        results = await repo.get_by_workflow("wf_123")
        assert len(results) == 1
        assert results[0].workflow_id == "wf_123"

    @pytest.mark.asyncio
    async def test_get_failed_runs(self):
        doc = make_agent_log_doc()
        doc["status"] = "failed"
        collection = make_mock_collection(find_return=[doc])
        repo = AgentLogRepository(collection)

        results = await repo.get_failed_runs()
        assert len(results) == 1
        assert results[0].status == AgentLogStatus.FAILED
        collection.find.assert_called_once_with({"status": "failed"})


class TestAuditLogRepository:
    @pytest.mark.asyncio
    async def test_create_audit(self):
        doc = make_audit_log_doc()
        collection = make_mock_collection(find_one_return=doc)
        repo = AuditLogRepository(collection)

        audit_create = AuditLogCreate(
            action="report_uploaded",
            resource_type="report",
        )
        result = await repo.create(audit_create)
        assert isinstance(result, AuditLogInDB)
        assert result.action == "report_uploaded"

    @pytest.mark.asyncio
    async def test_get_by_user(self):
        docs = [make_audit_log_doc()]
        collection = make_mock_collection(find_return=docs)
        repo = AuditLogRepository(collection)

        results = await repo.get_by_user("507f1f77bcf86cd799439001")
        assert len(results) == 1
        assert results[0].user_id == "507f1f77bcf86cd799439001"

    @pytest.mark.asyncio
    async def test_get_by_resource(self):
        docs = [make_audit_log_doc()]
        collection = make_mock_collection(find_return=docs)
        repo = AuditLogRepository(collection)

        results = await repo.get_by_resource("report", resource_id="report_123")
        assert len(results) == 1
        assert results[0].resource_type == "report"
        collection.find.assert_called_once_with({"resource_type": "report", "resource_id": "report_123"})
