"""
Nura - Patient Memory Models
MongoDB models for patient_memory collection
"""

from datetime import datetime, timezone
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict


def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


class PatientMemoryBase(BaseModel):
    """Base fields shared by patient memory models"""
    model_config = ConfigDict(populate_by_name=True)

    patient_id: str = Field(..., description="Reference to the patient user ID")
    ai_summary: Optional[str] = Field(None, description="Longitudinal AI summary")
    chronic_conditions: List[str] = Field(default_factory=list, description="List of chronic conditions")
    allergies: List[str] = Field(default_factory=list, description="List of allergies")
    medications: List[str] = Field(default_factory=list, description="List of current medications")
    surgeries: List[str] = Field(default_factory=list, description="List of past surgeries")
    diagnoses: List[str] = Field(default_factory=list, description="List of diagnoses")
    health_risks: List[str] = Field(default_factory=list, description="List of health risks")
    recent_findings: List[str] = Field(default_factory=list, description="List of recent findings")
    lifestyle_notes: Optional[str] = Field(None, description="Lifestyle notes")
    timeline: List[Any] = Field(default_factory=list, description="Timeline of important historical events")
    content_hash: Optional[str] = Field(None, description="Hash of patient memory sections for incremental updates")
    summary_version: int = Field(default=1, description="Incremental version number of patient memory")

    # New fields added for Sprint 5 Report Synchronization
    longitudinal_summary: Optional[str] = Field(None, description="Detailed overall health longitudinal summary")
    latest_report_summary: Optional[str] = Field(None, description="AI summary of the most recently processed report")
    latest_risk: Optional[str] = Field(None, description="Risk assessment level of the most recently processed report")
    laboratory_history: List[Dict[str, Any]] = Field(default_factory=list, description="Historical lab test parameters tracker")
    medication_history: List[Dict[str, Any]] = Field(default_factory=list, description="Historical list of medications prescribed")
    diagnosis_history: List[Dict[str, Any]] = Field(default_factory=list, description="Historical clinical diagnoses tracker")
    laboratory_trends: Optional[str] = Field(None, description="Calculated longitudinal lab value trends text")
    latest_recommendations: List[Dict[str, Any]] = Field(default_factory=list, description="Suggestions from the latest risk analysis run")
    procedures: List[str] = Field(default_factory=list, description="Extracted clinical procedures history")
    medical_history: List[str] = Field(default_factory=list, description="Textual patient history records")
    report_summaries: List[Dict[str, Any]] = Field(default_factory=list, description="History log of individual report summaries")


class PatientMemoryCreate(PatientMemoryBase):
    """Model used to create a new patient memory record"""
    pass


class PatientMemoryUpdate(BaseModel):
    """Model used to update an existing patient memory record"""
    ai_summary: Optional[str] = None
    chronic_conditions: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    medications: Optional[List[str]] = None
    surgeries: Optional[List[str]] = None
    diagnoses: Optional[List[str]] = None
    health_risks: Optional[List[str]] = None
    recent_findings: Optional[List[str]] = None
    lifestyle_notes: Optional[str] = None
    timeline: Optional[List[Any]] = None
    content_hash: Optional[str] = None
    summary_version: Optional[int] = None

    # New fields updates for Sprint 5
    longitudinal_summary: Optional[str] = None
    latest_report_summary: Optional[str] = None
    latest_risk: Optional[str] = None
    laboratory_history: Optional[List[Dict[str, Any]]] = None
    medication_history: Optional[List[Dict[str, Any]]] = None
    diagnosis_history: Optional[List[Dict[str, Any]]] = None
    laboratory_trends: Optional[str] = None
    latest_recommendations: Optional[List[Dict[str, Any]]] = None
    procedures: Optional[List[str]] = None
    medical_history: Optional[List[str]] = None
    report_summaries: Optional[List[Dict[str, Any]]] = None


class PatientMemoryInDB(PatientMemoryBase):
    """Patient memory as stored in MongoDB"""
    id: str = Field(..., description="Document ID")
    last_updated: datetime = Field(default_factory=utc_now, description="Last update timestamp")

    @classmethod
    def from_mongo(cls, data: dict) -> "PatientMemoryInDB":
        """Create PatientMemoryInDB from raw MongoDB document, converting ObjectId to str."""
        doc = dict(data)
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        if "patient_id" in doc and doc["patient_id"] is not None and not isinstance(doc["patient_id"], str):
            doc["patient_id"] = str(doc["patient_id"])
        
        # Safe timezone-aware mapping for last_updated
        if "last_updated" in doc:
            pass
        elif "updated_at" in doc:
            doc["last_updated"] = doc.pop("updated_at")
        
        return cls(**doc)
