"""
Nura - AI Schemas
Pydantic response and request models for AI health and playground test endpoints
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


class AIHealthResponse(BaseModel):
    """Schema representing AI infrastructure connectivity health status"""
    reachable: bool = Field(..., description="Indicates if the Groq API service is reachable")
    model: str = Field(..., description="The currently configured default model name")
    latency_ms: float = Field(..., description="Response latency of connectivity check in milliseconds")
    status: str = Field(..., description="General health state (healthy or unhealthy)")
    timestamp: str = Field(..., description="ISO 8601 formatted UTC check timestamp")


class AITestRequest(BaseModel):
    """Schema for requesting a direct AI prompt generation verification test"""
    prompt: str = Field(..., min_length=1, description="Raw prompt text payload to run against the LLM")


class TokenUsage(BaseModel):
    """Token accounting details for a request execution"""
    prompt_tokens: int = Field(..., description="Tokens utilized in the input prompt request")
    completion_tokens: int = Field(..., description="Tokens generated in the response completion payload")
    total_tokens: int = Field(..., description="Aggregated total tokens processed")


class AITestResponse(BaseModel):
    """Orchestrated response metrics for prompt generation testing"""
    response: str = Field(..., description="LLM generated string response text")
    model: str = Field(..., description="Specific model utilized during prompt processing")
    token_usage: TokenUsage = Field(..., description="Detailed token consumption figures")
    latency: float = Field(..., description="Roundtrip processing time in milliseconds")
    finish_reason: str = Field(..., description="Execution boundary completion condition (e.g. stop, length)")


class AIExecutionSession(BaseModel):
    """Telemetry log session tracking AI orchestrator query details"""
    request_id: str = Field(..., description="Unique trace identifier")
    user_id: Optional[str] = Field(None, description="Request caller user ID")
    patient_id: Optional[str] = Field(None, description="Target patient user ID context")
    model: str = Field(..., description="Configured model name utilized")
    start_time: datetime = Field(..., description="Pipeline execution start timestamp")
    end_time: datetime = Field(..., description="Pipeline execution end timestamp")
    duration: float = Field(..., description="Total elapsed pipeline execution duration in milliseconds")
    tokens: int = Field(..., description="Total token consumption count")
    cost: float = Field(..., description="Computed financial cost in USD")
    status: str = Field(..., description="Final status: success or failed")
    errors: Optional[str] = Field(None, description="Detailed stacktrace/message if failed")


class AIPlaygroundChatRequest(BaseModel):
    """Request query payload for AI integration chat testing"""
    prompt: str = Field(..., min_length=1, description="User query text")
    patient_id: Optional[str] = Field(None, description="Optional target patient ID for context compilation")
    model: Optional[str] = Field(None, description="Override LLM model name")
    temperature: Optional[float] = Field(None, description="LLM temperature override parameter")
    max_tokens: Optional[int] = Field(None, description="LLM max tokens limit parameter")


class AIPlaygroundChatResponse(BaseModel):
    """Response payload containing LLM output, execution session telemetry, and trace prompts details"""
    response: str = Field(..., description="Output content completed by the model")
    execution_session: AIExecutionSession = Field(..., description="Telemetry details of execution pipeline run")
    prompt_template: str = Field(..., description="Final compiled prompt payload sent to LLM")
    patient_context_sections: List[str] = Field(default_factory=list, description="List of patient context sections loaded")


class AIPlaygroundHealthResponse(BaseModel):
    """Consolidated health report checks mapping all AI infrastructure components"""
    groq: Dict[str, Any] = Field(..., description="Groq API connection status details")
    embedding: Dict[str, Any] = Field(..., description="Embedding engine status details")
    vector: Dict[str, Any] = Field(..., description="Vector database client health details")
    prompt_registry: Dict[str, Any] = Field(..., description="Prompt templates file configuration status details")
    context_builder: Dict[str, Any] = Field(..., description="Context compiler DB connectivity details")




