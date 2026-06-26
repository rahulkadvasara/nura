"""
Nura - Patient Context Schemas
Pydantic schemas for patient context assembly and metadata
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PatientContextMetadata(BaseModel):
    """Metadata detailing the context builder execution"""
    patient_id: str = Field(..., description="Target patient user ID")
    generated_at: datetime = Field(..., description="Timestamp when context was generated")
    sources_used: List[str] = Field(..., description="MongoDB collections queried during assembly")
    sections_returned: List[str] = Field(..., description="Non-empty context sections included in payload")
    estimated_tokens: int = Field(..., description="Estimated token count of the structured context")
    context_version: str = Field(default="1.0.0", description="Version of context layout specification")


class PatientContextResponse(BaseModel):
    """Unified structured healthcare profile context data"""
    patient_profile: Optional[Dict[str, Any]] = Field(None, description="Patient basic user info")
    medical_summary: Optional[str] = Field(None, description="Longitudinal patient summary from memory")
    current_conditions: List[str] = Field(default_factory=list, description="Chronic diseases and diagnoses list")
    past_medical_history: List[str] = Field(default_factory=list, description="Surgeries and timeline events history")
    current_medications: List[str] = Field(default_factory=list, description="Active drug medications list")
    medication_allergies: List[str] = Field(default_factory=list, description="Known drug and medical allergies list")
    drug_allergies: List[str] = Field(default_factory=list, description="Known chemical/drug allergies list")
    lab_reports_summary: List[Dict[str, Any]] = Field(default_factory=list, description="Recent laboratory/imaging reports list")
    appointments_summary: List[Dict[str, Any]] = Field(default_factory=list, description="Recent appointments list")
    consultations_summary: List[Dict[str, Any]] = Field(default_factory=list, description="Recent doctor consultation visits list")
    prescriptions_summary: List[Dict[str, Any]] = Field(default_factory=list, description="Recent prescriptions list")
    reminder_summary: List[Dict[str, Any]] = Field(default_factory=list, description="Active reminders list")
    recent_health_insights: List[Dict[str, Any]] = Field(default_factory=list, description="Recent AI health insights list")
    lifestyle_notes: Optional[str] = Field(None, description="Lifestyle/habit details from memory")
    emergency_information: Optional[str] = Field(None, description="Critical risk summaries or emergency context")
    risk_factors: List[str] = Field(default_factory=list, description="General health risk flags list")
    
    metadata: PatientContextMetadata = Field(..., description="Context assembly performance and provenance metadata")
