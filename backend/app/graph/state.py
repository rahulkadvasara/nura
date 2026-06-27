"""
Nura - LangGraph State
Definition of strongly typed shared execution state dictionary mappings.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class GraphState(BaseModel):
    """
    State model representing the complete pipeline execution details.
    Must be serializable and support future agents without modification.
    """
    request_id: Optional[str] = Field(default=None, description="Unique execution request transaction ID")
    session_id: Optional[str] = Field(default=None, description="Active chat session/thread identifier")
    conversation_id: Optional[str] = Field(default=None, description="Underlying conversation thread identifier")
    patient_id: Optional[str] = Field(default=None, description="Associated patient profile identifier")
    doctor_id: Optional[str] = Field(default=None, description="Associated doctor profile identifier")
    user_id: Optional[str] = Field(default=None, description="Triggers caller identifier")
    role: Optional[str] = Field(default=None, description="Role of the triggering user")
    query: Optional[str] = Field(default=None, description="Raw input text query")
    detected_intent: Optional[str] = Field(default=None, description="Intent classified for routing")
    selected_agent: Optional[str] = Field(default=None, description="Agent selected for execution")
    retrieved_context: Optional[str] = Field(default=None, description="Assembled semantic search chunks context")
    patient_context: Optional[str] = Field(default=None, description="MongoDB longitudinal patient clinical profile summary")
    messages: List[Dict[str, Any]] = Field(default_factory=list, description="Historical chat messages in execution queue")
    response: Optional[str] = Field(default=None, description="Final generated output string text")
    citations: List[Dict[str, Any]] = Field(default_factory=list, description="Citations mapping references list")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom payload variables dictionary")
    execution_trace: List[str] = Field(default_factory=list, description="Order log list of nodes traversed")
    token_usage: Dict[str, int] = Field(default_factory=dict, description="LLM execution tokens mapping (prompt, completion, total)")
    execution_time: float = Field(default=0.0, description="Total execution latency in milliseconds")
    current_node: Optional[str] = Field(default=None, description="Currently executing graph node ID")
    previous_node: Optional[str] = Field(default=None, description="Previously executed graph node ID")
    error: Optional[str] = Field(default=None, description="Trace message text of exceptions/failures")
    debug_mode: bool = Field(default=False, description="Flag indicating cache-bypass debug trace mode")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize state object back to standard dictionary"""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GraphState":
        """Deserialize state class instance from standard dictionary parameters"""
        return cls(**data)
