"""
Nura - AI Schemas
Pydantic response and request models for AI health and playground test endpoints
"""

from pydantic import BaseModel, Field


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
