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
    return ReportResponse(
        id=report.id,
        patient_id=report.patient_id,
        uploaded_by=report.uploaded_by,
        report_type=report.report_type,
        file_url=report.file_url,
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
    ):
        super().__init__()
        self.report_repository = report_repository
        self.user_repository = user_repository

    async def create_report(
        self,
        schema: ReportCreateSchema,
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

        result = await self.report_repository.collection.insert_one(doc_dict)
        created = await self.report_repository.collection.find_one({"_id": result.inserted_id})
        if created is None:
            raise RuntimeError("Report was inserted but could not be retrieved")
        return ReportInDB.from_mongo(created)

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
        return await self.report_repository.update(report_id, update)

    async def delete_report(self, report_id: str) -> bool:
        """Permanently delete a report record"""
        return await self.report_repository.delete(report_id)

    def to_response(self, report: ReportInDB) -> ReportResponse:
        """Convert internal model to API response"""
        return _report_to_response(report)
