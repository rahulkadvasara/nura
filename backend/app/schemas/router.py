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
