"""
Nura - Multi-Agent Orchestrator API Schemas
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class AIExecuteRequest(BaseModel):
    """Payload requesting multi-agent workflow pipeline execution"""
    query: str = Field(..., min_length=1, description="Raw input text query")
    patient_id: Optional[str] = Field(default=None, description="Optional Patient MongoDB reference identifier")
    session_id: Optional[str] = Field(default=None, description="Optional Chat session thread ID")
    conversation_id: Optional[str] = Field(default=None, description="Optional Conversation thread ID")
    debug_mode: bool = Field(default=False, description="Enables verbose debugging response trace")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary context")


class StandardResponseContract(BaseModel):
    """Standardized unified response schema returned for all AI execute queries"""
    success: bool = Field(..., description="Flag indicating if execution finished successfully")
    agent: Optional[str] = Field(default=None, description="Selected agent mapped from registry that executed")
    intent: Optional[str] = Field(default=None, description="Winning classified intent name")
    response: Optional[str] = Field(default=None, description="Final generated output text string")
    citations: List[Dict[str, Any]] = Field(default_factory=list, description="Citations mapping references list")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary context")
    usage: Dict[str, int] = Field(default_factory=dict, description="LLM execution tokens mapping (prompt, completion, total)")
    execution_trace: List[str] = Field(default_factory=list, description="Order log list of nodes traversed")
    execution_time: float = Field(default=0.0, description="Total execution latency in milliseconds")
    cost: float = Field(default=0.0, description="Estimated total cost of the LLM call")
    warnings: List[str] = Field(default_factory=list, description="Specific warning notices list")


class OrchestratorStatisticsResponse(BaseModel):
    """Payload returning cumulative multi-agent orchestrator statistics"""
    total_executions: int = Field(..., description="Total executions run count")
    intent_distribution: Dict[str, int] = Field(..., description="Counts of intent names traversal")
    agent_usage: Dict[str, int] = Field(..., description="Counts of agent executions")
    average_latency_ms: float = Field(..., description="Average latency in milliseconds")
    total_token_usage: Dict[str, int] = Field(..., description="Accumulated token count totals")
    total_costs: float = Field(..., description="Accumulated USD cost estimation totals")
    failures: int = Field(..., description="Total failed requests")
    retries: int = Field(..., description="Total transient retries executed")
    cache_hit_rate: float = Field(..., description="RAGCache hit rate estimation")
    retrieval_metrics: Dict[str, Any] = Field(..., description="RAG search metrics summary")
