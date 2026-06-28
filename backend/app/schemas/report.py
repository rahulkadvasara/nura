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
    
    # OCR Pipeline processing fields
    ocr_status: Optional[str] = Field(None, description="OCR processing status")
    ocr_method: Optional[str] = Field(None, description="OCR extraction method")
    ocr_started_at: Optional[datetime] = Field(None, description="OCR started timestamp")
    ocr_completed_at: Optional[datetime] = Field(None, description="OCR completed timestamp")
    ocr_duration_ms: Optional[float] = Field(None, description="OCR execution duration in milliseconds")
    ocr_average_confidence: Optional[float] = Field(None, description="Average OCR confidence score (0.0 to 1.0)")
    page_count: Optional[int] = Field(None, description="Total pages extracted")
    normalized_text: Optional[str] = Field(None, description="Normalized extracted layout text")
    ocr_version: Optional[str] = Field(None, description="OCR processing pipeline version")
    processing_errors: Optional[List[str]] = Field(None, description="List of processing errors encountered")
    ocr_pages: Optional[List[Dict[str, Any]]] = Field(None, description="Raw text and confidence score breakdown per page")

    # Medical Extraction Pipeline fields
    document_type: Optional[str] = Field(None, description="Automatically classified report type")
    laboratory_results: Optional[List[Dict[str, Any]]] = Field(None, description="List of parsed laboratory test result objects")
    medications: Optional[List[Dict[str, Any]]] = Field(None, description="List of parsed medication prescription objects")
    diagnoses: Optional[List[str]] = Field(None, description="Consolidated list of diagnoses strings")
    allergies: Optional[List[str]] = Field(None, description="Consolidated list of allergies strings")
    extraction_status: Optional[str] = Field(None, description="Extraction pipeline status")
    extraction_confidence: Optional[float] = Field(None, description="Cumulative average confidence score")
    extraction_version: Optional[str] = Field(None, description="Extraction pipeline version")
    extraction_warnings: Optional[List[str]] = Field(None, description="List of validation warning logs")

    # Clinical Risk Analysis Pipeline fields
    risk_analysis: Optional[Dict[str, Any]] = Field(None, description="Detailed clinical risk analysis payload")
    overall_risk: Optional[str] = Field(None, description="Report aggregate risk category")
    risk_score: Optional[float] = Field(None, description="Calculated aggregate risk score")
    risk_findings: Optional[List[Dict[str, Any]]] = Field(None, description="List of identified specific risk details")
    recommendations: Optional[List[Dict[str, Any]]] = Field(None, description="List of structured recommendations details")
    clinical_flags: Optional[List[str]] = Field(None, description="Badges of triggered risk markers")
    risk_version: Optional[str] = Field(None, description="Clinical risk evaluation rule-engine version")
    risk_generated_at: Optional[datetime] = Field(None, description="Risk calculation timestamp")

    # Clinical AI Summarization fields
    patient_summary: Optional[str] = Field(None, description="Patient-friendly clinical report explanation")
    doctor_summary: Optional[str] = Field(None, description="Doctor-focused clinical diagnostic summary")
    key_findings: Optional[List[str]] = Field(None, description="List of most critical findings observed")
    clinical_insights: Optional[List[str]] = Field(None, description="Possible trends, complications and monitoring metrics")
    followup_questions: Optional[List[str]] = Field(None, description="Educational questions the patient can ask their physician")
    summary_confidence: Optional[float] = Field(None, description="Overall LLM generation confidence score")
    summary_version: Optional[str] = Field(None, description="AI summary prompt template version")
    summary_generated_at: Optional[datetime] = Field(None, description="AI summary generation timestamp")


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
    
    # OCR pipeline updates
    ocr_status: Optional[str] = None
    ocr_method: Optional[str] = None
    ocr_started_at: Optional[datetime] = None
    ocr_completed_at: Optional[datetime] = None
    ocr_duration_ms: Optional[float] = None
    ocr_average_confidence: Optional[float] = None
    page_count: Optional[int] = None
    normalized_text: Optional[str] = None
    ocr_version: Optional[str] = None
    processing_errors: Optional[List[str]] = None
    ocr_pages: Optional[List[Dict[str, Any]]] = None

    # Medical Extraction pipeline updates
    document_type: Optional[str] = None
    laboratory_results: Optional[List[Dict[str, Any]]] = None
    medications: Optional[List[Dict[str, Any]]] = None
    diagnoses: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    extraction_status: Optional[str] = None
    extraction_confidence: Optional[float] = None
    extraction_version: Optional[str] = None
    extraction_warnings: Optional[List[str]] = None

    # Clinical Risk Analysis pipeline updates
    risk_analysis: Optional[Dict[str, Any]] = None
    overall_risk: Optional[str] = None
    risk_score: Optional[float] = None
    risk_findings: Optional[List[Dict[str, Any]]] = None
    recommendations: Optional[List[Dict[str, Any]]] = None
    clinical_flags: Optional[List[str]] = None
    risk_version: Optional[str] = None
    risk_generated_at: Optional[datetime] = None

    # Clinical AI Summarization updates
    patient_summary: Optional[str] = None
    doctor_summary: Optional[str] = None
    key_findings: Optional[List[str]] = None
    clinical_insights: Optional[List[str]] = None
    followup_questions: Optional[List[str]] = None
    summary_confidence: Optional[float] = None
    summary_version: Optional[str] = None
    summary_generated_at: Optional[datetime] = None


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
    
    # OCR Pipeline fields
    ocr_status: Optional[str] = Field(None, description="OCR processing status")
    ocr_method: Optional[str] = Field(None, description="OCR extraction method")
    ocr_started_at: Optional[datetime] = Field(None, description="OCR started timestamp")
    ocr_completed_at: Optional[datetime] = Field(None, description="OCR completed timestamp")
    ocr_duration_ms: Optional[float] = Field(None, description="OCR execution duration in milliseconds")
    ocr_average_confidence: Optional[float] = Field(None, description="Average OCR confidence score (0.0 to 1.0)")
    page_count: Optional[int] = Field(None, description="Total pages extracted")
    normalized_text: Optional[str] = Field(None, description="Normalized extracted layout text")
    ocr_version: Optional[str] = Field(None, description="OCR processing pipeline version")
    processing_errors: Optional[List[str]] = Field(None, description="List of processing errors encountered")
    ocr_pages: Optional[List[Dict[str, Any]]] = Field(None, description="Raw text and confidence score breakdown per page")

    # Medical Extraction Pipeline fields
    document_type: Optional[str] = Field(None, description="Automatically classified report type")
    laboratory_results: Optional[List[Dict[str, Any]]] = Field(None, description="List of parsed laboratory test result objects")
    medications: Optional[List[Dict[str, Any]]] = Field(None, description="List of parsed medication prescription objects")
    diagnoses: Optional[List[str]] = Field(None, description="Consolidated list of diagnoses strings")
    allergies: Optional[List[str]] = Field(None, description="Consolidated list of allergies strings")
    extraction_status: Optional[str] = Field(None, description="Extraction pipeline status")
    extraction_confidence: Optional[float] = Field(None, description="Cumulative average confidence score")
    extraction_version: Optional[str] = Field(None, description="Extraction pipeline version")
    extraction_warnings: Optional[List[str]] = Field(None, description="List of validation warning logs")

    # Clinical Risk Analysis Pipeline fields
    risk_analysis: Optional[Dict[str, Any]] = Field(None, description="Detailed clinical risk analysis payload")
    overall_risk: Optional[str] = Field(None, description="Report aggregate risk category")
    risk_score: Optional[float] = Field(None, description="Calculated aggregate risk score")
    risk_findings: Optional[List[Dict[str, Any]]] = Field(None, description="List of identified specific risk details")
    recommendations: Optional[List[Dict[str, Any]]] = Field(None, description="List of structured recommendations details")
    clinical_flags: Optional[List[str]] = Field(None, description="Badges of triggered risk markers")
    risk_version: Optional[str] = Field(None, description="Clinical risk evaluation rule-engine version")
    risk_generated_at: Optional[datetime] = Field(None, description="Risk calculation timestamp")

    # Clinical AI Summarization fields
    patient_summary: Optional[str] = Field(None, description="Patient-friendly clinical report explanation")
    doctor_summary: Optional[str] = Field(None, description="Doctor-focused clinical diagnostic summary")
    key_findings: Optional[List[str]] = Field(None, description="List of most critical findings observed")
    clinical_insights: Optional[List[str]] = Field(None, description="Possible trends, complications and monitoring metrics")
    followup_questions: Optional[List[str]] = Field(None, description="Educational questions the patient can ask their physician")
    summary_confidence: Optional[float] = Field(None, description="Overall LLM generation confidence score")
    summary_version: Optional[str] = Field(None, description="AI summary prompt template version")
    summary_generated_at: Optional[datetime] = Field(None, description="AI summary generation timestamp")


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
