"""
Nura - Observability and Audit Models
MongoDB models for agent_logs and audit_logs collections
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class AgentLogStatus(str, Enum):
    """Execution status of an AI agent or RAG workflow"""
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Agent Log Models
# ---------------------------------------------------------------------------

class AgentLogBase(BaseModel):
    """Base fields shared by agent log models"""
    model_config = ConfigDict(populate_by_name=True)

    agent_name: str = Field(..., description="Name of the agent executing (e.g. router_agent)")
    workflow_id: str = Field(..., description="Unique ID grouping steps in a workflow execution")
    session_id: Optional[str] = Field(None, description="Optional chat session ID reference")
    patient_id: Optional[str] = Field(None, description="Optional patient user ID reference")
    user_id: Optional[str] = Field(None, description="Optional triggering user ID reference")
    input_payload: Dict[str, Any] = Field(default_factory=dict, description="Input parameters / prompts")
    output_payload: Dict[str, Any] = Field(default_factory=dict, description="Generated response / output data")
    status: AgentLogStatus = Field(default=AgentLogStatus.STARTED, description="Execution status")
    latency_ms: float = Field(default=0.0, ge=0.0, description="Execution time in milliseconds")
    token_usage: Dict[str, int] = Field(default_factory=dict, description="LLM token counts (prompt, completion, total)")
    error_message: Optional[str] = Field(None, description="Error trace / message if status is failed")

    # Future AI Observability Preparation (Task 7 Design Fields)
    langgraph_thread_id: Optional[str] = Field(None, description="Proactive preparation for LangGraph checkpoint threads")
    langgraph_checkpoint_id: Optional[str] = Field(None, description="Proactive preparation for LangGraph execution state checkpoints")
    langfuse_trace_id: Optional[str] = Field(None, description="Proactive preparation for LangFuse trace integration")
    langfuse_parent_observation_id: Optional[str] = Field(None, description="Proactive preparation for LangFuse span/node observation references")
    orchestrator_node: Optional[str] = Field(None, description="Proactive preparation for agent routing node identification")
    evaluation_metrics: Dict[str, Any] = Field(default_factory=dict, description="Proactive preparation for faithfulness, relevance, or LLM-as-a-judge scores")
    research_metadata: Dict[str, Any] = Field(default_factory=dict, description="Proactive preparation for research cohort and analytics metrics")


class AgentLogCreate(AgentLogBase):
    """Model used to initialize an agent log record"""
    pass


class AgentLogUpdate(BaseModel):
    """Model used to update an agent log record status and output"""
    output_payload: Optional[Dict[str, Any]] = None
    status: Optional[AgentLogStatus] = None
    latency_ms: Optional[float] = Field(None, ge=0.0)
    token_usage: Optional[Dict[str, int]] = None
    error_message: Optional[str] = None
    langgraph_thread_id: Optional[str] = None
    langgraph_checkpoint_id: Optional[str] = None
    langfuse_trace_id: Optional[str] = None
    langfuse_parent_observation_id: Optional[str] = None
    orchestrator_node: Optional[str] = None
    evaluation_metrics: Optional[Dict[str, Any]] = None
    research_metadata: Optional[Dict[str, Any]] = None


class AgentLogInDB(AgentLogBase):
    """Agent log as stored in MongoDB"""
    id: str = Field(..., description="Document ID")
    created_at: datetime = Field(default_factory=utc_now, description="Log creation timestamp")

    @classmethod
    def from_mongo(cls, data: dict) -> "AgentLogInDB":
        """Create AgentLogInDB from raw MongoDB document, converting ObjectId to str."""
        doc = dict(data)
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        for field in ("session_id", "patient_id", "user_id"):
            if field in doc and doc[field] is not None and not isinstance(doc[field], str):
                doc[field] = str(doc[field])
        return cls(**doc)


# ---------------------------------------------------------------------------
# Audit Log Models
# ---------------------------------------------------------------------------

class AuditLogBase(BaseModel):
    """Base fields shared by audit log models"""
    model_config = ConfigDict(populate_by_name=True)

    user_id: Optional[str] = Field(None, description="User ID who executed the action (None if system/anon)")
    action: str = Field(..., description="Name of the audited action (e.g. profile_updated, report_uploaded)")
    resource_type: str = Field(..., description="Target entity type (e.g. user, report, appointment)")
    resource_id: Optional[str] = Field(None, description="Target entity ID reference")
    old_value: Optional[Any] = Field(None, description="Pre-action state / value")
    new_value: Optional[Any] = Field(None, description="Post-action state / value")
    ip_address: Optional[str] = Field(None, description="IP address of the client triggering the action")
    user_agent: Optional[str] = Field(None, description="Browser / client user agent details")


class AuditLogCreate(AuditLogBase):
    """Model used to insert a new audit log record"""
    pass


class AuditLogUpdate(BaseModel):
    """Audit logs are immutable but repository updates require base structure matching"""
    pass


class AuditLogInDB(AuditLogBase):
    """Audit log as stored in MongoDB"""
    id: str = Field(..., description="Document ID")
    created_at: datetime = Field(default_factory=utc_now, description="Audit timestamp")

    @classmethod
    def from_mongo(cls, data: dict) -> "AuditLogInDB":
        """Create AuditLogInDB from raw MongoDB document, converting ObjectId to str."""
        doc = dict(data)
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        for field in ("user_id", "resource_id"):
            if field in doc and doc[field] is not None and not isinstance(doc[field], str):
                doc[field] = str(doc[field])
        return cls(**doc)
