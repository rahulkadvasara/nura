"""
Nura - Observability and Audit Schemas
Pydantic v2 schemas for agent run logs and audit logs requests and responses
"""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict

from app.models.observability import AgentLogStatus


# ---------------------------------------------------------------------------
# Agent Log Schemas
# ---------------------------------------------------------------------------

class AgentLogCreateSchema(BaseModel):
    """Request schema for creating an agent log record"""
    agent_name: str = Field(..., description="Name of the executing agent")
    workflow_id: str = Field(..., description="Unique ID for workflow trace grouping")
    session_id: Optional[str] = Field(None, description="Associated chat session ID")
    patient_id: Optional[str] = Field(None, description="Associated patient ID")
    user_id: Optional[str] = Field(None, description="Triggering user ID")
    input_payload: Dict[str, Any] = Field(default_factory=dict, description="Input payload / inputs")
    output_payload: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Output payload / responses")
    status: AgentLogStatus = Field(default=AgentLogStatus.STARTED, description="Initial execution state")
    latency_ms: float = Field(default=0.0, ge=0.0, description="Latency in milliseconds")
    token_usage: Optional[Dict[str, int]] = Field(default_factory=dict, description="Token counts details")
    error_message: Optional[str] = Field(None, description="Error message if run failed")

    # Future AI Observability Preparation (Task 7 Design Fields)
    langgraph_thread_id: Optional[str] = Field(None, description="LangGraph thread checkout ID")
    langgraph_checkpoint_id: Optional[str] = Field(None, description="LangGraph execution state ID")
    langfuse_trace_id: Optional[str] = Field(None, description="LangFuse tracing link")
    langfuse_parent_observation_id: Optional[str] = Field(None, description="LangFuse parent step locator")
    orchestrator_node: Optional[str] = Field(None, description="Agent node router location")
    evaluation_metrics: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Relevance / metrics score card")
    research_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Research metrics logs")


class AgentLogUpdateSchema(BaseModel):
    """Request schema for updating an agent log state"""
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


class AgentLogResponse(BaseModel):
    """Response schema representing an agent execution record"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    id: str = Field(..., description="Agent log record ID")
    agent_name: str = Field(..., description="Agent name identifier")
    workflow_id: str = Field(..., description="Workflow ID grouping")
    session_id: Optional[str] = Field(None)
    patient_id: Optional[str] = Field(None)
    user_id: Optional[str] = Field(None)
    input_payload: Dict[str, Any] = Field(..., description="Inputs parameters")
    output_payload: Dict[str, Any] = Field(..., description="Outputs generated")
    status: AgentLogStatus = Field(..., description="State of execution")
    latency_ms: float = Field(..., description="Duration in milliseconds")
    token_usage: Dict[str, int] = Field(..., description="LLM token counts details")
    error_message: Optional[str] = Field(None)

    # Future AI Observability Preparation (Task 7 Design Fields)
    langgraph_thread_id: Optional[str] = Field(None)
    langgraph_checkpoint_id: Optional[str] = Field(None)
    langfuse_trace_id: Optional[str] = Field(None)
    langfuse_parent_observation_id: Optional[str] = Field(None)
    orchestrator_node: Optional[str] = Field(None)
    evaluation_metrics: Dict[str, Any] = Field(default_factory=dict)
    research_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(..., description="Log creation timestamp")


# ---------------------------------------------------------------------------
# Audit Log Schemas
# ---------------------------------------------------------------------------

class AuditLogCreateSchema(BaseModel):
    """Request schema for inserting a new audit trail record"""
    user_id: Optional[str] = Field(None, description="User performing the action (None if system/anon)")
    action: str = Field(..., description="Audited activity identifier")
    resource_type: str = Field(..., description="Resource collection name")
    resource_id: Optional[str] = Field(None, description="Resource identifier ID")
    old_value: Optional[Any] = Field(None, description="Previous state properties")
    new_value: Optional[Any] = Field(None, description="Modified state properties")
    ip_address: Optional[str] = Field(None, description="Client IP address context")
    user_agent: Optional[str] = Field(None, description="Client Browser context")


class AuditLogUpdateSchema(BaseModel):
    """Audit logs are immutable but repository updates require base structure matching"""
    pass


class AuditLogResponse(BaseModel):
    """Response schema representing an audited activity log"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    id: str = Field(..., description="Audit record ID")
    user_id: Optional[str] = Field(None)
    action: str = Field(..., description="Activity identifier name")
    resource_type: str = Field(..., description="Resource target collection")
    resource_id: Optional[str] = Field(None)
    old_value: Optional[Any] = Field(None)
    new_value: Optional[Any] = Field(None)
    ip_address: Optional[str] = Field(None)
    user_agent: Optional[str] = Field(None)
    created_at: datetime = Field(..., description="Audit timestamp")
