"""
Nura - Router Endpoints API Schemas
Pydantic validation schemas for Router REST administrative endpoints.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class RouterIntentsResponse(BaseModel):
    """Payload returning all registered intents and agent mappings configuration"""
    supported_intents: List[str] = Field(..., description="List of all supported intents")
    registered_agents: Dict[str, str] = Field(..., description="Active Intent-to-Agent registry mappings")
    routing_rules: Dict[str, Any] = Field(..., description="Active configuration thresholds and settings parameters")


class RouterClassifyRequest(BaseModel):
    """Payload requesting query classification check"""
    query: str = Field(..., min_length=1, description="Prompt query text to classify")


class RouterClassifyResponse(BaseModel):
    """Payload returning classification check results"""
    detected_intent: str = Field(..., description="Winning classified intent name")
    confidence: float = Field(..., description="Confidence probability calculation rating")
    matched_rules: List[str] = Field(..., description="Rules triggered during analysis")
    selected_agent: str = Field(..., description="Target downstream execution agent name")


class RouterTestRequest(BaseModel):
    """Payload requesting full routing pipeline execution run check"""
    query: str = Field(..., min_length=1, description="Prompt query text to run through routing pipeline")
    patient_id: Optional[str] = Field(default=None, description="Optional Patient MongoDB reference identifier")
    debug_mode: Optional[bool] = Field(default=False, description="Enables verbose logging responses")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata dictionary context")



class RouterTestResponse(BaseModel):
    """Payload returning routing pipeline execution results"""
    graph_trace: List[str] = Field(..., description="Log trace of executed nodes order in state graph run")
    routing_trace: List[str] = Field(..., description="List of matched classification rules details")
    detected_intent: str = Field(..., description="Winning classified intent name")
    selected_agent: str = Field(..., description="Selected agent mapped from registry")
    confidence: float = Field(..., description="Winning confidence level")
    latency_ms: float = Field(..., description="Overall routing latency in milliseconds")


class RouterStatisticsResponse(BaseModel):
    """Payload returning cumulative router telemetry metrics"""
    total_routed_requests: int = Field(..., description="Total routed requests count")
    average_routing_latency_ms: float = Field(..., description="Average routing latency in milliseconds")
    confidence_distribution: Dict[str, int] = Field(..., description="Counts of classifications per confidence level")
    intent_distribution: Dict[str, int] = Field(..., description="Counts of classifications per intent name category")
    unknown_queries_count: int = Field(..., description="Total routed queries categorized as unknown")
    unknown_percentage: float = Field(..., description="Percentage of unknown routed queries")
    fallback_count: int = Field(..., description="Total routed queries utilizing fallback")
    fallback_percentage: float = Field(..., description="Percentage of fallback executions")
    routing_failures_count: int = Field(..., description="Total routing failures logged")


class MedicalKnowledgeAgentResponse(BaseModel):
    """Output schema for MedicalKnowledgeAgent"""
    answer: str = Field(..., description="Grounded response text to the medical question")
    citations: List[Dict[str, Any]] = Field(default_factory=list, description="Citations and evidence reference details list")
    confidence: float = Field(..., description="Confidence score probability of the response (0.0 to 1.0)")
    sources: List[str] = Field(default_factory=list, description="List of Qdrant collections or source names queried")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary context")
    usage: Dict[str, int] = Field(default_factory=dict, description="LLM execution tokens mapping (prompt, completion, total)")


class SymptomAgentResponse(BaseModel):
    """Output schema for SymptomAgent"""
    summary: str = Field(..., description="Brief symptom analysis summary text containing informational safety notices")
    possible_causes: List[str] = Field(default_factory=list, description="List of potential clinical causes")
    red_flags: List[str] = Field(default_factory=list, description="List of clinical red flags detected")
    recommended_action: str = Field(..., description="Suggested clinical actions or escalation recommendations")
    emergency: bool = Field(default=False, description="Emergency escalation warning flag")
    citations: List[Dict[str, Any]] = Field(default_factory=list, description="Citations reference list")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary context")
    usage: Dict[str, int] = Field(default_factory=dict, description="LLM execution tokens mapping (prompt, completion, total)")


class MemoryAgentResponse(BaseModel):
    """Output schema for MemoryAgent"""
    memory_summary: str = Field(..., description="Grounded AI longitudinal patient memory summary text")
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="Recent conversation messages history list")
    patient_summary: str = Field(..., description="Deterministic aggregated patient summary text from builder")
    relevant_context: List[Dict[str, Any]] = Field(default_factory=list, description="Semantic memories retrieved from Qdrant")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary context")

