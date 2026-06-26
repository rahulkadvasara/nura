"""
Nura - Agent Response
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict

class AgentResponse(BaseModel):
    """Standardized response schema returned by every AI agent in the platform"""
    model_config = ConfigDict(populate_by_name=True)

    success: bool = Field(..., description="Flag indicating if the execution was successful")
    message: str = Field(..., description="Status description message")
    response: Any = Field(..., description="Structured or raw output of the agent execution")
    citations: List[str] = Field(default_factory=list, description="References or data source citations utilized")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata returned with execution payload")
    usage: Dict[str, Any] = Field(
        default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        description="Model token usages breakdown if LLM generation was performed"
    )
    execution_time: float = Field(..., description="Total execution latency duration in milliseconds")
    agent_name: str = Field(..., description="Name of the executing agent")
