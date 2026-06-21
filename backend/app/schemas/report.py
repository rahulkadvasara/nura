"""
Nura - Medical Report and Health Insight Schemas
Pydantic v2 schemas for report and health insight API requests and responses
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict

from app.models.report import (
    ReportType,
    ProcessingStatus,
    RiskLevel,
    InsightType,
    Severity,
)


# ---------------------------------------------------------------------------
# Report Schemas
# ---------------------------------------------------------------------------

class ReportCreateSchema(BaseModel):
    """Request schema for uploading/creating a new report metadata record"""
    patient_id: str = Field(..., description="Reference to the patient user ID")
    uploaded_by: str = Field(..., description="Reference to the user ID who uploaded the report")
    report_type: ReportType = Field(default=ReportType.OTHER, description="Type of medical report")
    file_url: str = Field(..., description="URL of the uploaded report file")
    raw_text: Optional[str] = Field(None, description="Extracted raw text from OCR")
    structured_data: Optional[Dict[str, Any]] = Field(None, description="Extracted structured metrics")
    entities: Optional[List[Dict[str, Any]]] = Field(None, description="Extracted medical entities")
    ai_summary: Optional[str] = Field(None, description="AI-generated summary of the report")
    risk_level: RiskLevel = Field(default=RiskLevel.LOW, description="Report risk classification")
    processing_status: ProcessingStatus = Field(default=ProcessingStatus.UPLOADED, description="Processing status")


class ReportUpdateSchema(BaseModel):
    """Request schema for updating report metadata or processing details"""
    patient_id: Optional[str] = None
    uploaded_by: Optional[str] = None
    report_type: Optional[ReportType] = None
    file_url: Optional[str] = None
    raw_text: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    entities: Optional[List[Dict[str, Any]]] = None
    ai_summary: Optional[str] = None
    risk_level: Optional[RiskLevel] = None
    processing_status: Optional[ProcessingStatus] = None


class ReportResponse(BaseModel):
    """Response schema for a medical report"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    id: str = Field(..., description="Report ID")
    patient_id: str = Field(..., description="Patient user ID")
    uploaded_by: str = Field(..., description="Uploading user ID")
    report_type: ReportType = Field(..., description="Type of medical report")
    file_url: str = Field(..., description="URL of the report file")
    raw_text: Optional[str] = Field(None, description="Extracted raw text from OCR")
    structured_data: Optional[Dict[str, Any]] = Field(None, description="Extracted structured metrics")
    entities: Optional[List[Dict[str, Any]]] = Field(None, description="Extracted medical entities")
    ai_summary: Optional[str] = Field(None, description="AI-generated summary of the report")
    risk_level: RiskLevel = Field(..., description="Report risk classification")
    processing_status: ProcessingStatus = Field(..., description="Processing status")
    created_at: datetime = Field(..., description="Report creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# ---------------------------------------------------------------------------
# Health Insight Schemas
# ---------------------------------------------------------------------------

class HealthInsightCreateSchema(BaseModel):
    """Request schema for creating a health insight"""
    patient_id: str = Field(..., description="Reference to the patient user ID")
    insight_type: InsightType = Field(..., description="Type of health insight")
    title: str = Field(..., min_length=1, max_length=200, description="Title of the insight")
    description: str = Field(..., min_length=1, max_length=2000, description="Description of the insight")
    severity: Severity = Field(default=Severity.LOW, description="Severity of the insight")
    source_report_id: Optional[str] = Field(None, description="Optional reference to the source report ID")


class HealthInsightUpdateSchema(BaseModel):
    """Request schema for updating a health insight"""
    patient_id: Optional[str] = None
    insight_type: Optional[InsightType] = None
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=2000)
    severity: Optional[Severity] = None
    source_report_id: Optional[str] = None


class HealthInsightResponse(BaseModel):
    """Response schema for a health insight"""
    model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat()})

    id: str = Field(..., description="Health Insight ID")
    patient_id: str = Field(..., description="Patient user ID")
    insight_type: InsightType = Field(..., description="Type of health insight")
    title: str = Field(..., description="Title of the insight")
    description: str = Field(..., description="Description of the insight")
    severity: Severity = Field(..., description="Severity of the insight")
    source_report_id: Optional[str] = Field(None, description="Optional reference to source report ID")
    created_at: datetime = Field(..., description="Insight creation timestamp")
