"""
Nura - Core Agents Response Schemas
Strongly-typed validation models for core knowledge agents outputs.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


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
