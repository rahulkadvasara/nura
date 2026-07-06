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
    get_risk_analysis_service,
    get_report_understanding_service,
    get_report_sync_service,
    get_report_sync_validator,
    get_patient_memory_repository,
    get_pipeline_service,
    get_pipeline_validator,
    get_pipeline_telemetry,
    get_report_progress_tracker,
    get_background_telemetry,
    get_report_queue_manager,
    get_report_cache_service,
    get_job_dispatcher,
    get_worker_scheduler,
    get_storage_service,
)
from app.services.storage.storage_provider import StorageProvider
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
    pipeline_service = Depends(get_pipeline_service),
    storage_service: StorageProvider = Depends(get_storage_service),
) -> SuccessResponse:
    try:
        # Enforce patient restriction (Patients can only upload reports for themselves)
        if current_user.role == UserRole.PATIENT and str(current_user.id) != patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Patients are only authorized to upload reports for themselves"
            )

        from bson import ObjectId
        # Pre-allocate report ID to build deterministic bucket path: patients/{patient_id}/{report_id}.pdf
        report_id = str(ObjectId())
        ext = os.path.splitext(file.filename)[1].lower() or ".pdf"
        object_key = f"patients/{patient_id}/{report_id}{ext}"

        # Clean/Upload file through storage abstraction layer
        upload_res = await storage_service.upload_file(
            file=file.file,
            filename=object_key,
            bucket="reports",
            content_type=file.content_type,
            original_filename=file.filename
        )

        # 2. Ingest report record in MongoDB
        schema = ReportCreateSchema(
            patient_id=patient_id,
            uploaded_by=str(current_user.id),
            report_type=report_type,
            file_url=upload_res["public_url"] or f"reports/{object_key}", # Fallback for private Supabase URLs
            file_metadata=upload_res,
            raw_text=None,
            structured_data=None,
            entities=None,
            ai_summary=None,
            risk_level=RiskLevel.LOW,
            processing_status=ProcessingStatus.UPLOADED,
            ocr_status="pending",
            ocr_pages=[]
        )
        report_record = await report_service.create_report(schema, report_id=report_id)

        # 3. Auto-trigger end-to-end medical orchestrator pipeline in the background
        background_tasks.add_task(pipeline_service.execute_pipeline, report_record.id)

        return SuccessResponse(
            success=True,
            message="Report file uploaded and orchestrator pipeline scheduled successfully",
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
    storage_service: StorageProvider = Depends(get_storage_service),
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
    
    # Clean up file in storage provider
    if success:
        if report.file_metadata:
            try:
                meta = report.file_metadata
                await storage_service.delete_file(
                    bucket=meta.get("bucket", "reports"),
                    object_key=meta.get("object_key")
                )
            except Exception as e:
                logger.error(f"Failed to delete report file using metadata: {e}")
        elif report.file_url:
            if not report.file_url.startswith("http"):
                # Clean up local file path
                if os.path.exists(report.file_url):
                    try:
                        os.remove(report.file_url)
                    except Exception:
                        pass
            else:
                # Attempt standard deletion by parsing basename
                try:
                    old_filename = os.path.basename(report.file_url)
                    await storage_service.delete_file(bucket="reports", object_key=old_filename)
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


@router.post(
    "/{report_id}/risk-analysis",
    response_model=SuccessResponse,
    summary="Trigger clinical risk analysis for a report. Guarded: Authorized Users.",
)
async def analyze_report_clinical_risks(
    report_id: str,
    background_tasks: BackgroundTasks,
    current_user: UserInDB = Depends(get_current_user),
    report_service: ReportService = Depends(get_report_service),
    risk_service = Depends(get_risk_analysis_service),
) -> SuccessResponse:
    report = await report_service.get_report_by_id(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Authorize access
    await verify_report_access(report, current_user)

    # Trigger risk analysis in background tasks
    background_tasks.add_task(risk_service.analyze_report_risks, report_id)

    return SuccessResponse(
        success=True,
        message="Clinical risk analysis task triggered successfully"
    )


@router.get(
    "/{report_id}/risk",
    response_model=SuccessResponse,
    summary="Get calculated clinical risk analysis and recommendations. Guarded: Authorized Users.",
)
async def get_report_risks(
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

    risk_data = {
        "report_id": report_id,
        "overall_risk": getattr(report, "overall_risk", "NORMAL") or "NORMAL",
        "risk_score": getattr(report, "risk_score", 0.0) or 0.0,
        "risk_findings": getattr(report, "risk_findings", []) or [],
        "recommendations": getattr(report, "recommendations", []) or [],
        "clinical_flags": getattr(report, "clinical_flags", []) or [],
        "risk_analysis": getattr(report, "risk_analysis", {}) or {},
        "risk_version": getattr(report, "risk_version", "1.0.0") or "1.0.0",
        "risk_generated_at": getattr(report, "risk_generated_at", None),
        "processing_status": getattr(report, "processing_status", "pending") or "pending"
    }

    return SuccessResponse(
        success=True,
        message="Clinical risk analysis data retrieved successfully",
        data=risk_data
    )


@router.get(
    "/risk/statistics",
    response_model=SuccessResponse,
    summary="Retrieve cumulative clinical risk telemetry statistics. Guarded: Admin Only.",
)
async def get_risk_telemetry(
    current_user: UserInDB = Depends(get_current_user),
) -> SuccessResponse:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin accounts are authorized to view risk telemetry stats"
        )
    
    from app.services.report_risk.telemetry import get_report_risk_telemetry
    stats = get_report_risk_telemetry().get_stats()
    
    return SuccessResponse(
        success=True,
        message="Clinical risk telemetry statistics fetched successfully",
        data=stats
    )


@router.post(
    "/{report_id}/summarize",
    response_model=SuccessResponse,
    summary="Trigger clinical AI report understanding and summarization. Guarded: Authorized Users.",
)
async def summarize_report_clinical(
    report_id: str,
    background_tasks: BackgroundTasks,
    current_user: UserInDB = Depends(get_current_user),
    report_service: ReportService = Depends(get_report_service),
    understanding_service = Depends(get_report_understanding_service),
) -> SuccessResponse:
    report = await report_service.get_report_by_id(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Authorize access
    await verify_report_access(report, current_user)

    # Trigger summary analysis in background tasks
    background_tasks.add_task(understanding_service.generate_report_summary, report_id)

    return SuccessResponse(
        success=True,
        message="Clinical AI summarization task triggered successfully"
    )


@router.get(
    "/{report_id}/summary",
    response_model=SuccessResponse,
    summary="Get calculated clinical AI summaries. Guarded: Authorized Users.",
)
async def get_report_ai_summary(
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

    summary_data = {
        "report_id": report_id,
        "ai_summary": getattr(report, "ai_summary", "") or "",
        "patient_summary": getattr(report, "patient_summary", "") or "",
        "doctor_summary": getattr(report, "doctor_summary", "") or "",
        "summary_confidence": getattr(report, "summary_confidence", 0.0) or 0.0,
        "summary_version": getattr(report, "summary_version", "1.0.0") or "1.0.0",
        "summary_generated_at": getattr(report, "summary_generated_at", None)
    }

    return SuccessResponse(
        success=True,
        message="Clinical AI summaries data retrieved successfully",
        data=summary_data
    )


@router.get(
    "/{report_id}/insights",
    response_model=SuccessResponse,
    summary="Get calculated clinical AI insights and findings. Guarded: Authorized Users.",
)
async def get_report_ai_insights(
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

    insights_data = {
        "report_id": report_id,
        "key_findings": getattr(report, "key_findings", []) or [],
        "clinical_insights": getattr(report, "clinical_insights", []) or [],
        "followup_questions": getattr(report, "followup_questions", []) or []
    }

    return SuccessResponse(
        success=True,
        message="Clinical AI insights data retrieved successfully",
        data=insights_data
    )


@router.get(
    "/ai/statistics",
    response_model=SuccessResponse,
    summary="Retrieve cumulative clinical report AI telemetry statistics. Guarded: Admin Only.",
)
async def get_report_ai_telemetry_stats(
    current_user: UserInDB = Depends(get_current_user),
) -> SuccessResponse:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin accounts are authorized to view report AI telemetry stats"
        )
    
    from app.services.report_ai.telemetry import get_report_ai_telemetry
    stats = get_report_ai_telemetry().get_stats()
    
    return SuccessResponse(
        success=True,
        message="Clinical report AI telemetry statistics fetched successfully",
        data=stats
    )


@router.get(
    "/patient-memory",
    response_model=SuccessResponse,
    summary="Retrieve the patient memory profile for the logged in patient",
)
async def get_patient_memory(
    current_user: UserInDB = Depends(get_current_user),
    memory_repo = Depends(get_patient_memory_repository),
) -> SuccessResponse:
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patient accounts can fetch their patient memory"
        )
    
    memory = await memory_repo.get_by_patient_id(str(current_user.id))
    return SuccessResponse(
        success=True,
        message="Patient memory retrieved successfully",
        data=memory
    )


@router.get(
    "/synchronization/statistics",
    response_model=SuccessResponse,
    summary="Get cumulative report synchronization statistics. Guarded: Admin Only.",
)
async def get_report_sync_statistics(
    current_user: UserInDB = Depends(get_current_user),
) -> SuccessResponse:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin accounts can retrieve report sync statistics"
        )
    
    from app.services.report_sync.telemetry import get_report_sync_telemetry
    stats = get_report_sync_telemetry().get_statistics()
    return SuccessResponse(
        success=True,
        message="Synchronization statistics retrieved successfully",
        data=stats
    )


@router.post(
    "/synchronization/rebuild",
    response_model=SuccessResponse,
    summary="Rebuild synchronization index for all processed medical reports. Guarded: Admin Only.",
)
async def rebuild_report_synchronization(
    current_user: UserInDB = Depends(get_current_user),
    sync_service = Depends(get_report_sync_service),
) -> SuccessResponse:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin accounts are authorized to trigger index rebuilds"
        )
    
    res = await sync_service.rebuild_all_synchronizations()
    return SuccessResponse(
        success=True,
        message="Rebuild synchronization jobs executed",
        data=res
    )


@router.post(
    "/{report_id}/synchronize",
    response_model=SuccessResponse,
    summary="Trigger report summaries and metadata synchronization to patient memory and Qdrant",
)
async def synchronize_report(
    report_id: str,
    current_user: UserInDB = Depends(get_current_user),
    report_service = Depends(get_report_service),
    sync_service = Depends(get_report_sync_service),
) -> SuccessResponse:
    # Fetch report
    report = await report_service.get_report_by_id(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Authorize access
    await verify_report_access(report, current_user)

    res = await sync_service.synchronize_report(report_id)
    return SuccessResponse(
        success=True,
        message="Report synchronization completed successfully",
        data=res
    )


@router.get(
    "/{report_id}/sync-status",
    response_model=SuccessResponse,
    summary="Retrieve validation check status of report sync pipeline",
)
async def get_report_sync_status(
    report_id: str,
    current_user: UserInDB = Depends(get_current_user),
    report_service = Depends(get_report_service),
    validator = Depends(get_report_sync_validator),
) -> SuccessResponse:
    # Fetch report
    report = await report_service.get_report_by_id(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Authorize access
    await verify_report_access(report, current_user)

    res = await validator.validate_synchronization(report_id)
    return SuccessResponse(
        success=True,
        message="Report synchronization validation status retrieved",
        data=res
    )


@router.get(
    "/pipeline/statistics",
    response_model=SuccessResponse,
    summary="Get cumulative pipeline statistics and telemetry. Guarded: Admin Only.",
)
async def get_pipeline_statistics(
    current_user: UserInDB = Depends(get_current_user),
    telemetry = Depends(get_pipeline_telemetry),
) -> SuccessResponse:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin accounts can retrieve report pipeline statistics"
        )
    
    stats = await telemetry.get_statistics()
    return SuccessResponse(
        success=True,
        message="Pipeline statistics retrieved successfully",
        data=stats
    )


@router.get(
    "/{report_id}/pipeline",
    response_model=SuccessResponse,
    summary="Get current stage status and execution timings for a report pipeline.",
)
async def get_report_pipeline_status(
    report_id: str,
    current_user: UserInDB = Depends(get_current_user),
    report_service = Depends(get_report_service),
) -> SuccessResponse:
    report = await report_service.get_report_by_id(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    await verify_report_access(report, current_user)

    pipeline_data = {
        "report_id": report_id,
        "pipeline_status": getattr(report, "pipeline_status", "pending") or "pending",
        "processing_status": report.processing_status,
        "ocr_status": getattr(report, "ocr_status", "pending"),
        "extraction_status": getattr(report, "extraction_status", "pending"),
        "overall_risk": getattr(report, "overall_risk", None),
        "ai_summary": getattr(report, "ai_summary", None),
        "is_synchronized": getattr(report, "is_synchronized", False),
        "ocr_duration_ms": getattr(report, "ocr_duration_ms", 0.0),
        "extraction_duration_ms": getattr(report, "extraction_duration_ms", 0.0),
        "risk_duration_ms": getattr(report, "risk_duration_ms", 0.0),
        "summary_duration_ms": getattr(report, "summary_duration_ms", 0.0),
        "sync_duration_ms": getattr(report, "sync_duration_ms", 0.0),
        "pipeline_duration_ms": getattr(report, "pipeline_duration_ms", 0.0),
        "pipeline_errors": getattr(report, "pipeline_errors", []) or [],
        "pipeline_retries": getattr(report, "pipeline_retries", 0) or 0
    }

    return SuccessResponse(
        success=True,
        message="Report pipeline status fetched successfully",
        data=pipeline_data
    )


@router.post(
    "/{report_id}/pipeline/retry",
    response_model=SuccessResponse,
    summary="Trigger retry of failed stages in report processing pipeline.",
)
async def retry_failed_pipeline_stages(
    report_id: str,
    background_tasks: BackgroundTasks,
    current_user: UserInDB = Depends(get_current_user),
    report_service = Depends(get_report_service),
    pipeline_service = Depends(get_pipeline_service),
) -> SuccessResponse:
    report = await report_service.get_report_by_id(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    await verify_report_access(report, current_user)

    # Queue execution in background tasks
    background_tasks.add_task(pipeline_service.execute_pipeline, report_id, force_retry=True)

    return SuccessResponse(
        success=True,
        message="Pipeline retry execution triggered successfully in the background"
    )


@router.get(
    "/{report_id}/download",
    summary="Download or stream the original uploaded PDF/image file.",
)
async def download_original_report_file(
    report_id: str,
    current_user: UserInDB = Depends(get_current_user),
    report_service = Depends(get_report_service),
):
    from fastapi.responses import FileResponse
    report = await report_service.get_report_by_id(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    await verify_report_access(report, current_user)
    
    if not report.file_url or not os.path.exists(report.file_url):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original report file does not exist on disk"
        )
        
    return FileResponse(report.file_url)


# ============================================================
# Sprint 7 — Progress Tracking
# ============================================================

@router.get(
    "/{report_id}/progress",
    response_model=SuccessResponse,
    summary="Get real-time processing progress for a report. Guarded: Authenticated Users.",
)
async def get_report_progress(
    report_id: str,
    current_user: UserInDB = Depends(get_current_user),
    progress_tracker=Depends(get_report_progress_tracker),
    report_service: ReportService = Depends(get_report_service),
) -> SuccessResponse:
    report = await report_service.get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    await verify_report_access(report, current_user)
    progress = await progress_tracker.get_progress(report_id)
    return SuccessResponse(success=True, message="Progress retrieved", data=progress)


# ============================================================
# Sprint 7 — Batch Upload
# ============================================================

@router.post(
    "/batch",
    response_model=SuccessResponse,
    summary="Batch upload multiple medical report files. Guarded: Authenticated Users.",
)
async def batch_upload_reports(
    patient_id: str = Form(...),
    report_type: ReportType = Form(ReportType.OTHER),
    files: List[UploadFile] = File(...),
    current_user: UserInDB = Depends(get_current_user),
    report_service: ReportService = Depends(get_report_service),
    job_dispatcher=Depends(get_job_dispatcher),
    storage_service: StorageProvider = Depends(get_storage_service),
) -> SuccessResponse:
    if current_user.role == UserRole.PATIENT and str(current_user.id) != patient_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Patients can only upload for themselves")

    if len(files) > 10:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum 10 files per batch upload")

    results = []

    from bson import ObjectId
    for file in files:
        try:
            report_id = str(ObjectId())
            ext = os.path.splitext(file.filename)[1].lower() or ".pdf"
            object_key = f"patients/{patient_id}/{report_id}{ext}"

            upload_res = await storage_service.upload_file(
                file=file.file,
                filename=object_key,
                bucket="reports",
                content_type=file.content_type,
                original_filename=file.filename
            )

            schema = ReportCreateSchema(
                patient_id=patient_id,
                uploaded_by=str(current_user.id),
                report_type=report_type,
                file_url=upload_res["public_url"] or f"reports/{object_key}",
                file_metadata=upload_res,
                raw_text=None,
                structured_data=None,
                entities=None,
                ai_summary=None,
                risk_level=RiskLevel.LOW,
                processing_status=ProcessingStatus.UPLOADED,
                ocr_status="pending",
                ocr_pages=[],
            )
            report_record = await report_service.create_report(schema, report_id=report_id)
            job_id = await job_dispatcher.dispatch(
                report_id=report_record.id,
                patient_id=patient_id,
            )
            results.append({"filename": file.filename, "report_id": report_record.id, "job_id": job_id, "success": True})
        except Exception as e:
            logger.error(f"Batch upload failed for {file.filename}: {e}")
            results.append({"filename": file.filename, "success": False, "error": str(e)})

    return SuccessResponse(
        success=True,
        message=f"Batch upload completed: {sum(1 for r in results if r['success'])}/{len(files)} files queued",
        data={"reports": results},
    )


# ============================================================
# Sprint 7 — System Health & Monitoring APIs
# ============================================================

@router.get(
    "/system/health",
    response_model=SuccessResponse,
    summary="System health summary: queue, workers, cache. Guarded: Admin only.",
)
async def get_system_health(
    current_user: UserInDB = Depends(get_current_user),
    queue_manager=Depends(get_report_queue_manager),
    bg_telemetry=Depends(get_background_telemetry),
    cache_service=Depends(get_report_cache_service),
) -> SuccessResponse:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    queue_stats = await queue_manager.get_queue_stats()
    telemetry_stats = bg_telemetry.get_stats()
    cache_stats = cache_service.get_stats()

    failure_rate = telemetry_stats["throughput"]["failure_rate_percent"]
    health_status = "healthy" if failure_rate < 10 and queue_stats.get("dead_letter", 0) == 0 else "degraded"

    return SuccessResponse(
        success=True,
        message="System health retrieved",
        data={
            "health": health_status,
            "queue": queue_stats,
            "workers": telemetry_stats["workers"],
            "throughput": telemetry_stats["throughput"],
            "cache_sizes": cache_stats,
        },
    )


@router.get(
    "/system/workers",
    response_model=SuccessResponse,
    summary="Worker pool status and heartbeats. Guarded: Admin only.",
)
async def get_worker_status(
    current_user: UserInDB = Depends(get_current_user),
    scheduler=Depends(get_worker_scheduler),
) -> SuccessResponse:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    worker_status = scheduler.get_worker_status()
    heartbeats = await scheduler.get_heartbeats()

    return SuccessResponse(
        success=True,
        message="Worker status retrieved",
        data={
            "total_workers": scheduler.worker_count,
            "active_workers": scheduler.worker_count_active(),
            "idle_workers": scheduler.worker_count_idle(),
            "workers": worker_status,
            "heartbeats": heartbeats,
        },
    )


@router.get(
    "/system/queue",
    response_model=SuccessResponse,
    summary="Queue depth and recent failures. Guarded: Admin only.",
)
async def get_queue_stats(
    current_user: UserInDB = Depends(get_current_user),
    queue_manager=Depends(get_report_queue_manager),
) -> SuccessResponse:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    stats = await queue_manager.get_queue_stats()
    recent_failures = await queue_manager.get_recent_failures(limit=10)

    return SuccessResponse(
        success=True,
        message="Queue statistics retrieved",
        data={"stats": stats, "recent_failures": recent_failures},
    )


@router.get(
    "/system/cache",
    response_model=SuccessResponse,
    summary="Cache statistics: hit ratios and sizes. Guarded: Admin only.",
)
async def get_cache_stats(
    current_user: UserInDB = Depends(get_current_user),
    cache_service=Depends(get_report_cache_service),
    bg_telemetry=Depends(get_background_telemetry),
) -> SuccessResponse:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    full_stats = bg_telemetry.get_stats()
    size_stats = cache_service.get_stats()

    return SuccessResponse(
        success=True,
        message="Cache statistics retrieved",
        data={
            "hit_ratios": full_stats["cache"],
            "sizes": size_stats,
        },
    )
