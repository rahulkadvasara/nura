"""
Nura - Medical Report and Health Insight Models
MongoDB models for reports and health_insights collections
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ReportType(str, Enum):
    """Supported types of medical reports"""
    BLOOD_TEST = "blood_test"
    PRESCRIPTION = "prescription"
    IMAGING = "imaging"
    DISCHARGE_SUMMARY = "discharge_summary"
    OTHER = "other"


class ProcessingStatus(str, Enum):
    """Processing state of an uploaded report"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class RiskLevel(str, Enum):
    """Risk levels classified by analysis"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class InsightType(str, Enum):
    """Types of generated health insights"""
    TREND = "trend"
    ANOMALY = "anomaly"
    RECOMMENDATION = "recommendation"
    REMINDER = "reminder"


class Severity(str, Enum):
    """Severity classification for health insights"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

class ReportBase(BaseModel):
    """Base fields shared by medical report models"""
    model_config = ConfigDict(populate_by_name=True)

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
    ocr_status: Optional[str] = Field(None, description="OCR processing status: pending, processing, completed, failed")
    ocr_method: Optional[str] = Field(None, description="OCR extraction method: digital, ocr, none")
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
    document_type: Optional[str] = Field(None, description="Automatically classified report type (e.g. CBC, Lipid Profile)")
    laboratory_results: Optional[List[Dict[str, Any]]] = Field(None, description="List of parsed laboratory test result objects")
    medications: Optional[List[Dict[str, Any]]] = Field(None, description="List of parsed medication prescription objects")
    diagnoses: Optional[List[str]] = Field(None, description="Consolidated list of diagnoses strings")
    allergies: Optional[List[str]] = Field(None, description="Consolidated list of allergies strings")
    extraction_status: Optional[str] = Field(None, description="Extraction pipeline status: pending, processing, completed, failed")
    extraction_confidence: Optional[float] = Field(None, description="Cumulative average confidence of extracted sections")
    extraction_version: Optional[str] = Field(None, description="Medical information extraction pipeline version")
    extraction_warnings: Optional[List[str]] = Field(None, description="List of non-fatal validation warning logs")

    # Clinical Risk Analysis Pipeline fields
    risk_analysis: Optional[Dict[str, Any]] = Field(None, description="Detailed clinical risk analysis payload")
    overall_risk: Optional[str] = Field(None, description="Report aggregate risk category (NORMAL, LOW, MEDIUM, HIGH, CRITICAL)")
    risk_score: Optional[float] = Field(None, description="Calculated aggregate risk score (0.0 to 100.0)")
    risk_findings: Optional[List[Dict[str, Any]]] = Field(None, description="List of identified specific risk details")
    recommendations: Optional[List[Dict[str, Any]]] = Field(None, description="List of structured recommendations details")
    clinical_flags: Optional[List[str]] = Field(None, description="Badges of triggered risk markers")
    risk_version: Optional[str] = Field(None, description="Clinical risk evaluation rule-engine version")
    risk_generated_at: Optional[datetime] = Field(None, description="Risk calculation timestamp")


class ReportCreate(ReportBase):
    """Model used to create a new report record"""
    pass


class ReportUpdate(BaseModel):
    """Model used to update an existing report record"""
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


class ReportInDB(ReportBase):
    """Report as stored in MongoDB"""
    id: str = Field(..., description="Document ID")
    created_at: datetime = Field(default_factory=utc_now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=utc_now, description="Last update timestamp")

    @classmethod
    def from_mongo(cls, data: dict) -> "ReportInDB":
        """Create ReportInDB from raw MongoDB document, converting ObjectId to str."""
        doc = dict(data)
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        for field in ("patient_id", "uploaded_by"):
            if field in doc and doc[field] is not None and not isinstance(doc[field], str):
                doc[field] = str(doc[field])
        return cls(**doc)


# ---------------------------------------------------------------------------
# Health Insights
# ---------------------------------------------------------------------------

class HealthInsightBase(BaseModel):
    """Base fields shared by health insight models"""
    model_config = ConfigDict(populate_by_name=True)

    patient_id: str = Field(..., description="Reference to the patient user ID")
    insight_type: InsightType = Field(..., description="Type of health insight")
    title: str = Field(..., min_length=1, max_length=200, description="Title of the insight")
    description: str = Field(..., min_length=1, max_length=2000, description="Description of the insight")
    severity: Severity = Field(default=Severity.LOW, description="Severity of the insight")
    source_report_id: Optional[str] = Field(None, description="Optional reference to the source report ID")


class HealthInsightCreate(HealthInsightBase):
    """Model used to create a new health insight"""
    pass


class HealthInsightUpdate(BaseModel):
    """Model used to update an existing health insight"""
    patient_id: Optional[str] = None
    insight_type: Optional[InsightType] = None
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=2000)
    severity: Optional[Severity] = None
    source_report_id: Optional[str] = None


class HealthInsightInDB(HealthInsightBase):
    """Health insight as stored in MongoDB"""
    id: str = Field(..., description="Document ID")
    created_at: datetime = Field(default_factory=utc_now, description="Creation timestamp")

    @classmethod
    def from_mongo(cls, data: dict) -> "HealthInsightInDB":
        """Create HealthInsightInDB from raw MongoDB document, converting ObjectId to str."""
        doc = dict(data)
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        for field in ("patient_id", "source_report_id"):
            if field in doc and doc[field] is not None and not isinstance(doc[field], str):
                doc[field] = str(doc[field])
        return cls(**doc)
