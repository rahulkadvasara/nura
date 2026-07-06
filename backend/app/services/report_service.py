"""
Nura - Report Service
Business logic and validation for medical reports
"""

from datetime import datetime, timezone
from typing import List, Optional

from app.models.report import (
    ReportCreate,
    ReportUpdate,
    ReportInDB,
    ReportType,
    ProcessingStatus,
    RiskLevel,
)
from app.schemas.report import (
    ReportCreateSchema,
    ReportUpdateSchema,
    ReportResponse,
)
from app.repositories.report_repository import ReportRepository
from app.repositories.user_repository import UserRepository
from app.services.base import BaseService


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _report_to_response(report: ReportInDB) -> ReportResponse:
    file_url = report.file_url
    if report.file_metadata:
        try:
            from app.services.storage.storage_factory import get_storage_provider
            storage_service = get_storage_provider()
            meta = report.file_metadata
            if hasattr(meta, "bucket"):
                bucket = meta.bucket
                object_key = meta.object_key
            else:
                bucket = meta.get("bucket", "reports")
                object_key = meta.get("object_key")
            file_url = storage_service.generate_signed_url(bucket, object_key, expires_in=900)
        except Exception:
            pass

    return ReportResponse(
        id=report.id,
        patient_id=report.patient_id,
        uploaded_by=report.uploaded_by,
        report_type=report.report_type,
        file_url=file_url,
        file_metadata=report.file_metadata,
        raw_text=report.raw_text,
        structured_data=report.structured_data,
        entities=report.entities,
        ai_summary=report.ai_summary,
        risk_level=report.risk_level,
        processing_status=report.processing_status,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


class ReportService(BaseService[ReportInDB, ReportCreate, ReportUpdate]):
    """Service layer for medical report operations"""

    def __init__(
        self,
        report_repository: ReportRepository,
        user_repository: UserRepository,
        event_dispatcher = None,
    ):
        super().__init__()
        self.report_repository = report_repository
        self.user_repository = user_repository
        
        # Lazy load or use injected event dispatcher to prevent circular imports
        if event_dispatcher is None:
            try:
                from app.core.dependencies import get_event_dispatcher
                self.event_dispatcher = get_event_dispatcher()
            except ImportError:
                self.event_dispatcher = None
        else:
            self.event_dispatcher = event_dispatcher

    async def create_report(
        self,
        schema: ReportCreateSchema,
        report_id: Optional[str] = None
    ) -> ReportInDB:
        """Create a new report record after validating patient and uploader user existence"""
        # Validate patient exists
        patient = await self.user_repository.get(schema.patient_id)
        if not patient:
            raise ValueError(f"Patient user with ID {schema.patient_id} does not exist")

        # Validate uploaded_by user exists
        uploader = await self.user_repository.get(schema.uploaded_by)
        if not uploader:
            raise ValueError(f"Uploading user with ID {schema.uploaded_by} does not exist")

        now = utc_now()
        report_create = ReportCreate(
            patient_id=schema.patient_id,
            uploaded_by=schema.uploaded_by,
            report_type=schema.report_type,
            file_url=schema.file_url,
            file_metadata=schema.file_metadata,
            raw_text=schema.raw_text,
            structured_data=schema.structured_data,
            entities=schema.entities,
            ai_summary=schema.ai_summary,
            risk_level=schema.risk_level,
            processing_status=schema.processing_status,
        )

        doc_dict = report_create.model_dump()
        doc_dict["created_at"] = now
        doc_dict["updated_at"] = now

        if report_id:
            from bson import ObjectId
            doc_dict["_id"] = ObjectId(report_id)

        result = await self.report_repository.collection.insert_one(doc_dict)
        created = await self.report_repository.collection.find_one({"_id": result.inserted_id})
        if created is None:
            raise RuntimeError("Report was inserted but could not be retrieved")
            
        report_obj = ReportInDB.from_mongo(created)
        
        # Dispatch event
        if self.event_dispatcher:
            try:
                from app.events.base import ReportUploadedEvent
                event = ReportUploadedEvent(
                    patient_id=report_obj.patient_id,
                    report_id=report_obj.id,
                    uploaded_by=report_obj.uploaded_by
                )
                await self.event_dispatcher.dispatch(event)
            except Exception as e:
                import logging
                logging.getLogger("nura.services.report").error(f"Failed to dispatch ReportUploadedEvent: {e}")

        return report_obj

    async def get_report_by_id(self, report_id: str) -> Optional[ReportInDB]:
        """Fetch a report by its ID"""
        return await self.report_repository.get(report_id)

    async def list_reports(self, limit: int = 100, skip: int = 0) -> List[ReportInDB]:
        """List all reports"""
        return await self.report_repository.list(limit=limit, skip=skip)

    async def list_reports_by_patient(
        self,
        patient_id: str,
        limit: int = 100,
        skip: int = 0,
    ) -> List[ReportInDB]:
        """Fetch all reports for a patient"""
        return await self.report_repository.get_by_patient_id(patient_id, limit=limit, skip=skip)

    async def update_report(
        self,
        report_id: str,
        schema: ReportUpdateSchema,
    ) -> Optional[ReportInDB]:
        """Update an existing report record"""
        update = ReportUpdate(**schema.model_dump(exclude_unset=True))
        updated_report = await self.report_repository.update(report_id, update)
        
        # Dispatch event on status transition or update
        if updated_report and self.event_dispatcher:
            try:
                from app.events.base import ReportUploadedEvent
                event = ReportUploadedEvent(
                    patient_id=updated_report.patient_id,
                    report_id=updated_report.id,
                    uploaded_by=updated_report.uploaded_by
                )
                await self.event_dispatcher.dispatch(event)
            except Exception as e:
                import logging
                logging.getLogger("nura.services.report").error(f"Failed to dispatch ReportUploadedEvent on update: {e}")
                
        return updated_report

    async def delete_report(self, report_id: str) -> bool:
        """Permanently delete a report record"""
        return await self.report_repository.delete(report_id)

    def to_response(self, report: ReportInDB) -> ReportResponse:
        """Convert internal model to API response"""
        return _report_to_response(report)
