from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class DrugCheckRequest(BaseModel):
    medications: List[str] = Field(..., description="List of medications to check for interactions")

class InteractionPairDetail(BaseModel):
    drug_a: str = Field(..., description="Original name of Drug A")
    drug_a_normalized: str = Field(..., description="Normalized name of Drug A")
    drug_b: str = Field(..., description="Original name of Drug B")
    drug_b_normalized: str = Field(..., description="Normalized name of Drug B")
    severity: str = Field(..., description="Severity of the interaction (LOW, MEDIUM, HIGH, UNKNOWN)")
    description: str = Field(..., description="Detailed description of the interaction")

class DrugCheckResponse(BaseModel):
    medications: List[str] = Field(..., description="List of original medication names")
    normalized_medications: List[str] = Field(..., description="List of normalized medication names")
    detected_interactions: List[InteractionPairDetail] = Field(..., description="List of detected drug-drug interactions")
    severity: str = Field(..., description="Overall highest severity detected (LOW, MEDIUM, HIGH, UNKNOWN, NONE)")
    recommendations: List[str] = Field(..., description="Deterministic health recommendations")
    statistics: Dict[str, Any] = Field(..., description="Lookup and cache telemetry stats")
    latency_ms: float = Field(..., description="Inference execution duration in milliseconds")
