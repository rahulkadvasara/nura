"""
Nura - Healthcare Agents Response Schemas
Strongly-typed validation models for healthcare intelligence agents outputs.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ReportAnalysisAgentResponse(BaseModel):
    """Output schema for ReportAnalysisAgent"""
    summary: str = Field(..., description="Clear, patient-friendly summary of medical report analysis")
    key_findings: List[str] = Field(default_factory=list, description="Key medical findings extracted from the reports")
    abnormal_values: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted metrics showing abnormal clinical values")
    trend_analysis: List[str] = Field(default_factory=list, description="Trend patterns detected comparing recent and historical reports")
    recommendations: List[str] = Field(default_factory=list, description="Informational recommendations and next steps suggestions")
    citations: List[Dict[str, Any]] = Field(default_factory=list, description="Citations linking evidence chunks back to source reports")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary context")
    usage: Dict[str, int] = Field(default_factory=dict, description="LLM execution tokens mapping (prompt, completion, total)")


class DrugInteractionAgentResponse(BaseModel):
    """Output schema for DrugInteractionAgent"""
    interaction_found: bool = Field(..., description="Flag indicating if a potential safety conflict or interaction was identified")
    severity: str = Field(..., description="Severity classification of the interaction (LOW, MEDIUM, HIGH, CRITICAL)")
    interaction_summary: str = Field(..., description="Summary narrative of drug safety diagnostics and disclaimers")
    warnings: List[str] = Field(default_factory=list, description="Specific safety warning notices or contraindications list")
    alternatives: List[str] = Field(default_factory=list, description="Suggested medication alternatives to discuss with the physician")
    citations: List[Dict[str, Any]] = Field(default_factory=list, description="Citations to medical references utilized")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary context")
    usage: Dict[str, int] = Field(default_factory=dict, description="LLM execution tokens mapping (prompt, completion, total)")


class DoctorRecommendationAgentResponse(BaseModel):
    """Output schema for DoctorRecommendationAgent"""
    recommended_doctors: List[Dict[str, Any]] = Field(default_factory=list, description="Ranked list of recommended doctor profiles with availability")
    reasoning: str = Field(..., description="Aggregated recommendation reasoning details")
    matching_specialization: str = Field(..., description="Primary clinical specialization matched for symptoms")
    confidence: float = Field(..., description="Specialist matching confidence score (0.0 to 1.0)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary context")
    usage: Dict[str, int] = Field(default_factory=dict, description="LLM execution tokens mapping (prompt, completion, total)")
