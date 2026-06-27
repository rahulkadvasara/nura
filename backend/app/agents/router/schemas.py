"""
Nura - Router Agent API Schemas
Pydantic validation models for intent classification and routing results.
"""

from typing import List, Dict
from pydantic import BaseModel, Field


class IntentClassificationResult(BaseModel):
    """Result payload of the deterministic intent classifier"""
    intent: str = Field(..., description="Wining detected intent key name (e.g. MEDICAL_QUESTION)")
    confidence: float = Field(..., description="Computed classification confidence probability rating")
    matched_rules: List[str] = Field(default_factory=list, description="List of matched classifier keywords or regex patterns")
    candidate_intents: Dict[str, float] = Field(default_factory=dict, description="Intent candidates scores mapping")


class RoutingDecision(BaseModel):
    """Result payload of the router agent decision routing flow"""
    selected_agent: str = Field(..., description="Designated target agent mapped from registry (e.g. MedicalKnowledgeAgent)")
    detected_intent: str = Field(..., description="Winning intent categorized name")
    confidence: float = Field(..., description="Routing decision confidence rating")
    matched_rules: List[str] = Field(default_factory=list, description="Rules matched during evaluation")
