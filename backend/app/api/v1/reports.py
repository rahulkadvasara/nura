"""
Nura - Medical Reports and OCR REST API Endpoints Router
"""

import os
import shutil
import logging
import time
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks

from app.models.user import UserInDB, UserRole
from app.models.report import ReportInDB, ProcessingStatus, ReportType, RiskLevel
from app.schemas.auth import SuccessResponse
from app.schemas.report import ReportResponse, ReportCreateSchema
from app.core.dependencies import (
    get_current_user,
    get_report_service,
    get_document_parser,
    get_database,
    get_report_extraction_service,
)
from app.services.report_service import ReportService
from app.services.report_processing.document_parser import DocumentParser

logger = logging.getLogger("nura.api.reports")

router = APIRouter()

UPLOAD_DIR = "uploads/reports"


async def verify_report_access(report: ReportInDB, user: UserInDB) -> None:
    """Authorize access to report details. Admin, owner patient, or associated doctor only."""
    if user.role == UserRole.ADMIN:
        return
    if user.role == UserRole.PATIENT and str(user.id) == report.patient_id:
        return
    if user.role == UserRole.DOCTOR:
        db = get_database()
        # Verify if doctor has appointments or consultations with the patient owner
        doc_str = str(user.id)
        exists_app = await db.appointments.find_one({"doctor_id": doc_str, "patient_id": report.patient_id})
        if exists_app:
            return
        exists_cons = await db.consultations.find_one({"doctor_id": doc_str, "patient_id": report.patient_id})
        if exists_cons:
            return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Unauthorized to access this report processing data"
    )


@router.post(
    "/",
    response_model=SuccessResponse,
    summary="Upload a new medical report document. Guarded: Authenticated Users.",
)
async def upload_report(
    background_tasks: BackgroundTasks,
    patient_id: str = Form(..., description="Reference patient MongoDB ID"),
    report_type: ReportType = Form(ReportType.OTHER, description="Category of report"),
    file: UploadFile = File(..., description="PDF or Image report file"),
    current_user: UserInDB = Depends(get_current_user),
    report_service: ReportService = Depends(get_report_service),
    document_parser: DocumentParser = Depends(get_document_parser),
) -> SuccessResponse:
    try:
        # Enforce patient restriction (Patients can only upload reports for themselves)
        if current_user.role == UserRole.PATIENT and str(current_user.id) != patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Patients are only authorized to upload reports for themselves"
            )

        # 1. Save uploaded file locally
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(UPLOAD_DIR, f"{time.time()}_{file.filename}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 2. Ingest report record in MongoDB
        schema = ReportCreateSchema(
            patient_id=patient_id,
            uploaded_by=str(current_user.id),
            report_type=report_type,
            file_url=file_path,
            raw_text=None,
            structured_data=None,
            entities=None,
            ai_summary=None,
            risk_level=RiskLevel.LOW,
            processing_status=ProcessingStatus.UPLOADED,
            ocr_status="pending",
            ocr_pages=[]
        )
        report_record = await report_service.create_report(schema)

        # 3. Auto-trigger OCR processing pipeline in the background
        background_tasks.add_task(document_parser.process_report, report_record.id)

        return SuccessResponse(
            success=True,
            message="Report file uploaded and OCR queue processing scheduled successfully",
            data={"report": report_service.to_response(report_record).model_dump()}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to upload report document")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report ingestion failed: {str(e)}"
        )


@router.get(
    "/",
    response_model=SuccessResponse,
    summary="List medical reports. Guarded: Authenticated Users.",
)
async def list_reports(
    patient_id: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_user),
    report_service: ReportService = Depends(get_report_service),
) -> SuccessResponse:
    try:
        # Limit listings based on user role permissions
        if current_user.role == UserRole.PATIENT:
            # Patients can only list their own reports
            reports_list = await report_service.list_reports_by_patient(str(current_user.id))
        elif patient_id:
            reports_list = await report_service.list_reports_by_patient(patient_id)
        else:
            # Admins or doctors can list all reports if no patient filter is specified
            if current_user.role == UserRole.DOCTOR:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Doctors must specify patient_id filter to view records"
                )
            reports_list = await report_service.list_reports()

        res_list = [report_service.to_response(r).model_dump() for r in reports_list]

        return SuccessResponse(
            success=True,
            message="Reports retrieved successfully",
            data={"reports": res_list}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to fetch reports list")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch reports list: {str(e)}"
        )


@router.delete(
    "/{report_id}",
    response_model=SuccessResponse,
    summary="Delete a medical report. Guarded: Owner/Admin Only.",
)
async def delete_report(
    report_id: str,
    current_user: UserInDB = Depends(get_current_user),
    report_service: ReportService = Depends(get_report_service),
) -> SuccessResponse:
    report = await report_service.get_report_by_id(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Authorize deletion
    if current_user.role != UserRole.ADMIN and str(current_user.id) != report.patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized to delete this report record"
        )

    success = await report_service.delete_report(report_id)
    
    # Try deleting local file
    if success and report.file_url and os.path.exists(report.file_url):
        try:
            os.remove(report.file_url)
        except Exception:
            pass

    return SuccessResponse(
        success=success,
        message="Report deleted successfully" if success else "Failed to delete report"
    )


@router.post(
    "/{report_id}/process",
    response_model=SuccessResponse,
    summary="Manually trigger OCR processing for an uploaded report. Guarded: Authenticated Users.",
)
async def process_report(
    report_id: str,
    background_tasks: BackgroundTasks,
    current_user: UserInDB = Depends(get_current_user),
    report_service: ReportService = Depends(get_report_service),
    document_parser: DocumentParser = Depends(get_document_parser),
) -> SuccessResponse:
    report = await report_service.get_report_by_id(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Authorize access
    await verify_report_access(report, current_user)

    # Trigger OCR processing in background tasks
    background_tasks.add_task(document_parser.process_report, report_id)

    return SuccessResponse(
        success=True,
        message="OCR pipeline processing triggered successfully"
    )


@router.get(
    "/{report_id}/processing-status",
    response_model=SuccessResponse,
    summary="Get report OCR processing progress. Guarded: Authenticated Users.",
)
async def get_processing_status(
    report_id: str,
    current_user: UserInDB = Depends(get_current_user),
    report_service: ReportService = Depends(get_report_service),
) -> SuccessResponse:
    report = await report_service.get_report_by_id(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Authorize access
    await verify_report_access(report, current_user)

    # Return processing status metadata
    progress_data = {
        "report_id": report_id,
        "ocr_status": getattr(report, "ocr_status", "pending") or "pending",
        "processing_status": report.processing_status,
        "ocr_method": getattr(report, "ocr_method", "none") or "none",
        "page_count": getattr(report, "page_count", 0) or 0,
        "ocr_average_confidence": getattr(report, "ocr_average_confidence", 0.0) or 0.0,
        "ocr_duration_ms": getattr(report, "ocr_duration_ms", 0.0) or 0.0,
        "processing_errors": getattr(report, "processing_errors", []) or []
    }

    return SuccessResponse(
        success=True,
        message="Report processing status fetched successfully",
        data=progress_data
    )


@router.get(
    "/{report_id}/ocr",
    response_model=SuccessResponse,
    summary="Retrieve OCR text layout outputs. Guarded: Authorized Users Only.",
)
async def get_report_ocr(
    report_id: str,
    current_user: UserInDB = Depends(get_current_user),
    report_service: ReportService = Depends(get_report_service),
) -> SuccessResponse:
    report = await report_service.get_report_by_id(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Authorize access
    await verify_report_access(report, current_user)

    if getattr(report, "ocr_status", "pending") != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OCR processing is not completed for this report yet"
        )

    ocr_data = {
        "report_id": report_id,
        "raw_text": report.raw_text,
        "normalized_text": getattr(report, "normalized_text", None),
        "ocr_pages": getattr(report, "ocr_pages", []) or [],
        "metadata": {
            "ocr_method": getattr(report, "ocr_method", None),
            "ocr_completed_at": getattr(report, "ocr_completed_at", None),
            "ocr_average_confidence": getattr(report, "ocr_average_confidence", None),
            "page_count": getattr(report, "page_count", 0),
            "ocr_version": getattr(report, "ocr_version", None)
        }
    }

    return SuccessResponse(
        success=True,
        message="Report OCR data retrieved successfully",
        data=ocr_data
    )


@router.get(
    "/telemetry/statistics",
    response_model=SuccessResponse,
    summary="Retrieve cumulative OCR processing telemetry statistics. Guarded: Admin Only.",
)
async def get_processing_telemetry(
    current_user: UserInDB = Depends(get_current_user),
) -> SuccessResponse:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin accounts are authorized to view telemetry stats"
        )
    
    from app.services.report_processing.telemetry import get_report_processing_telemetry
    stats = get_report_processing_telemetry().get_stats()
    
    return SuccessResponse(
        success=True,
        message="Report processing telemetry fetched successfully",
        data=stats
    )


@router.post(
    "/{report_id}/extract",
    response_model=SuccessResponse,
    summary="Trigger clinical information extraction for OCR text. Guarded: Authenticated Users.",
)
async def extract_medical_report(
    report_id: str,
    background_tasks: BackgroundTasks,
    current_user: UserInDB = Depends(get_current_user),
    report_service: ReportService = Depends(get_report_service),
    extraction_service = Depends(get_report_extraction_service),
) -> SuccessResponse:
    report = await report_service.get_report_by_id(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Authorize access
    await verify_report_access(report, current_user)

    # Trigger medical extraction in background tasks
    background_tasks.add_task(extraction_service.extract_medical_information, report_id)

    return SuccessResponse(
        success=True,
        message="Medical information extraction task triggered successfully"
    )


@router.get(
    "/{report_id}/structured",
    response_model=SuccessResponse,
    summary="Get structured clinical results dataset. Guarded: Authorized Users.",
)
async def get_structured_data(
    report_id: str,
    current_user: UserInDB = Depends(get_current_user),
    report_service: ReportService = Depends(get_report_service),
) -> SuccessResponse:
    report = await report_service.get_report_by_id(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Authorize access
    await verify_report_access(report, current_user)

    structured = {
        "patient_information": getattr(report, "structured_data", {}).get("patient_information") if report.structured_data else None,
        "hospital_information": getattr(report, "structured_data", {}).get("hospital_information") if report.structured_data else None,
        "laboratory_results": getattr(report, "laboratory_results", []) or [],
        "medications": getattr(report, "medications", []) or [],
        "diagnoses": getattr(report, "diagnoses", []) or [],
        "allergies": getattr(report, "allergies", []) or [],
        "metadata": getattr(report, "structured_data", {}).get("metadata") if report.structured_data else {
            "extraction_method": "none",
            "extraction_version": "1.0.0",
            "confidence_score": 0.0
        },
        "extraction_warnings": getattr(report, "extraction_warnings", []) or [],
        "extraction_status": getattr(report, "extraction_status", "pending") or "pending",
        "document_type": getattr(report, "document_type", "Other") or "Other"
    }

    return SuccessResponse(
        success=True,
        message="Structured clinical report details fetched successfully",
        data=structured
    )


@router.get(
    "/{report_id}/entities",
    response_model=SuccessResponse,
    summary="Get extracted clinical entities list. Guarded: Authorized Users.",
)
async def get_report_entities(
    report_id: str,
    current_user: UserInDB = Depends(get_current_user),
    report_service: ReportService = Depends(get_report_service),
) -> SuccessResponse:
    report = await report_service.get_report_by_id(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Authorize access
    await verify_report_access(report, current_user)

    entities_list = getattr(report, "entities", []) or []

    return SuccessResponse(
        success=True,
        message="Extracted clinical entities list fetched successfully",
        data={"entities": entities_list}
    )


@router.get(
    "/telemetry/extraction",
    response_model=SuccessResponse,
    summary="Retrieve cumulative clinical extraction telemetry statistics. Guarded: Admin Only.",
)
async def get_extraction_telemetry(
    current_user: UserInDB = Depends(get_current_user),
) -> SuccessResponse:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin accounts are authorized to view telemetry stats"
        )
    
    from app.services.report_extraction.telemetry import get_report_extraction_telemetry
    stats = get_report_extraction_telemetry().get_stats()
    
    return SuccessResponse(
        success=True,
        message="Report extraction telemetry fetched successfully",
        data=stats
    )

