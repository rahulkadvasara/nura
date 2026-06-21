"""
Nura - Observability and Audit Models Tests
Tests for agent_logs and audit_logs Pydantic models
"""

import pytest
from datetime import datetime, timezone
from bson import ObjectId

from app.models.observability import (
    AgentLogStatus,
    AgentLogCreate,
    AgentLogUpdate,
    AgentLogInDB,
    AuditLogCreate,
    AuditLogUpdate,
    AuditLogInDB,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TestObservabilityEnums:
    def test_agent_log_status_values(self):
        assert AgentLogStatus.STARTED == "started"
        assert AgentLogStatus.COMPLETED == "completed"
        assert AgentLogStatus.FAILED == "failed"


class TestAgentLogModel:
    def test_create_agent_log(self):
        log = AgentLogCreate(
            agent_name="router_agent",
            workflow_id="wf_123",
            session_id="session_123",
            patient_id="patient_123",
            user_id="user_123",
            input_payload={"query": "hello"},
            output_payload={"response": "hi"},
            status=AgentLogStatus.COMPLETED,
            latency_ms=150.0,
            token_usage={"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7},
            error_message=None,
            langgraph_thread_id="thread_abc",
            langgraph_checkpoint_id="chk_xyz",
            langfuse_trace_id="trace_111",
            langfuse_parent_observation_id="obs_222",
            orchestrator_node="node_router",
            evaluation_metrics={"faithfulness": 1.0},
            research_metadata={"cohort": "A"},
        )
        assert log.agent_name == "router_agent"
        assert log.workflow_id == "wf_123"
        assert log.status == AgentLogStatus.COMPLETED
        assert log.latency_ms == 150.0
        assert log.token_usage == {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7}
        assert log.langgraph_thread_id == "thread_abc"
        assert log.langfuse_trace_id == "trace_111"
        assert log.orchestrator_node == "node_router"
        assert log.evaluation_metrics == {"faithfulness": 1.0}
        assert log.research_metadata == {"cohort": "A"}

    def test_agent_log_default_values(self):
        log = AgentLogCreate(
            agent_name="symptom_agent",
            workflow_id="wf_000",
        )
        assert log.session_id is None
        assert log.patient_id is None
        assert log.user_id is None
        assert log.input_payload == {}
        assert log.output_payload == {}
        assert log.status == AgentLogStatus.STARTED
        assert log.latency_ms == 0.0
        assert log.token_usage == {}
        assert log.error_message is None
        assert log.langgraph_thread_id is None
        assert log.langfuse_trace_id is None

    def test_agent_log_in_db_from_mongo(self):
        now = utc_now()
        raw = {
            "_id": ObjectId("507f1f77bcf86cd799439080"),
            "agent_name": "med_agent",
            "workflow_id": "wf_abc",
            "session_id": ObjectId("507f1f77bcf86cd799439001"),
            "patient_id": ObjectId("507f1f77bcf86cd799439002"),
            "user_id": ObjectId("507f1f77bcf86cd799439003"),
            "input_payload": {},
            "output_payload": {},
            "status": "started",
            "latency_ms": 0.0,
            "token_usage": {},
            "error_message": None,
            "created_at": now,
        }
        log = AgentLogInDB.from_mongo(raw)
        assert log.id == "507f1f77bcf86cd799439080"
        assert log.session_id == "507f1f77bcf86cd799439001"
        assert log.patient_id == "507f1f77bcf86cd799439002"
        assert log.user_id == "507f1f77bcf86cd799439003"
        assert log.created_at == now


class TestAuditLogModel:
    def test_create_audit_log(self):
        log = AuditLogCreate(
            user_id="user_123",
            action="profile_updated",
            resource_type="user",
            resource_id="user_123",
            old_value={"name": "Old"},
            new_value={"name": "New"},
            ip_address="127.0.0.1",
            user_agent="Firefox",
        )
        assert log.user_id == "user_123"
        assert log.action == "profile_updated"
        assert log.resource_type == "user"
        assert log.resource_id == "user_123"
        assert log.old_value == {"name": "Old"}
        assert log.new_value == {"name": "New"}
        assert log.ip_address == "127.0.0.1"
        assert log.user_agent == "Firefox"

    def test_audit_log_default_values(self):
        log = AuditLogCreate(
            action="report_uploaded",
            resource_type="report",
        )
        assert log.user_id is None
        assert log.resource_id is None
        assert log.old_value is None
        assert log.new_value is None
        assert log.ip_address is None
        assert log.user_agent is None

    def test_audit_log_in_db_from_mongo(self):
        now = utc_now()
        raw = {
            "_id": ObjectId("507f1f77bcf86cd799439080"),
            "user_id": ObjectId("507f1f77bcf86cd799439001"),
            "action": "doctor_verified",
            "resource_type": "doctor_profile",
            "resource_id": ObjectId("507f1f77bcf86cd799439002"),
            "created_at": now,
        }
        log = AuditLogInDB.from_mongo(raw)
        assert log.id == "507f1f77bcf86cd799439080"
        assert log.user_id == "507f1f77bcf86cd799439001"
        assert log.resource_id == "507f1f77bcf86cd799439002"
        assert log.created_at == now
