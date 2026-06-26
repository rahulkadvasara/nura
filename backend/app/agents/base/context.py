"""
Nura - Agent Context
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class AgentContext(BaseModel):
    """Context holding request metadata, session parameters, and user scopes for agent execution"""
    model_config = ConfigDict(populate_by_name=True)

    user_id: Optional[str] = Field(None, description="The authenticated user's ID")
    patient_id: Optional[str] = Field(None, description="The patient's ID context")
    doctor_id: Optional[str] = Field(None, description="The doctor's ID context")
    session_id: Optional[str] = Field(None, description="The chat session or operation ID")
    request_id: Optional[str] = Field(None, description="Unique trace request ID")
    role: Optional[str] = Field(None, description="User role associated with execution context")
    conversation_id: Optional[str] = Field(None, description="Active conversation identifier")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary custom logging context metadata")
