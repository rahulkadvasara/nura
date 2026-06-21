"""
Nura - Health Insight Service
Business logic and validation for health insights
"""

from datetime import datetime, timezone
from typing import List, Optional

from app.models.report import (
    HealthInsightCreate,
    HealthInsightUpdate,
    HealthInsightInDB,
    InsightType,
    Severity,
)
from app.schemas.report import (
    HealthInsightCreateSchema,
    HealthInsightUpdateSchema,
    HealthInsightResponse,
)
from app.repositories.health_insight_repository import HealthInsightRepository
from app.repositories.user_repository import UserRepository
from app.repositories.report_repository import ReportRepository
from app.services.base import BaseService


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _insight_to_response(insight: HealthInsightInDB) -> HealthInsightResponse:
    return HealthInsightResponse(
        id=insight.id,
        patient_id=insight.patient_id,
        insight_type=insight.insight_type,
        title=insight.title,
        description=insight.description,
        severity=insight.severity,
        source_report_id=insight.source_report_id,
        created_at=insight.created_at,
    )


class HealthInsightService(BaseService[HealthInsightInDB, HealthInsightCreate, HealthInsightUpdate]):
    """Service layer for health insight operations"""

    def __init__(
        self,
        health_insight_repository: HealthInsightRepository,
        user_repository: UserRepository,
        report_repository: ReportRepository,
    ):
        super().__init__()
        self.health_insight_repository = health_insight_repository
        self.user_repository = user_repository
        self.report_repository = report_repository

    async def create_insight(
        self,
        schema: HealthInsightCreateSchema,
    ) -> HealthInsightInDB:
        """Create a new health insight after validating patient and source report existence"""
        # Validate patient exists
        patient = await self.user_repository.get(schema.patient_id)
        if not patient:
            raise ValueError(f"Patient user with ID {schema.patient_id} does not exist")

        # Validate source report exists (if provided)
        if schema.source_report_id:
            report = await self.report_repository.get(schema.source_report_id)
            if not report:
                raise ValueError(f"Source report with ID {schema.source_report_id} does not exist")

        now = utc_now()
        insight_create = HealthInsightCreate(
            patient_id=schema.patient_id,
            insight_type=schema.insight_type,
            title=schema.title,
            description=schema.description,
            severity=schema.severity,
            source_report_id=schema.source_report_id,
        )

        doc_dict = insight_create.model_dump()
        doc_dict["created_at"] = now

        result = await self.health_insight_repository.collection.insert_one(doc_dict)
        created = await self.health_insight_repository.collection.find_one({"_id": result.inserted_id})
        if created is None:
            raise RuntimeError("Health insight was inserted but could not be retrieved")
        return HealthInsightInDB.from_mongo(created)

    async def get_insight_by_id(self, insight_id: str) -> Optional[HealthInsightInDB]:
        """Fetch a health insight by its ID"""
        return await self.health_insight_repository.get(insight_id)

    async def list_insights(self, limit: int = 100, skip: int = 0) -> List[HealthInsightInDB]:
        """List all health insights"""
        return await self.health_insight_repository.list(limit=limit, skip=skip)

    async def list_insights_by_patient(
        self,
        patient_id: str,
        limit: int = 100,
        skip: int = 0,
    ) -> List[HealthInsightInDB]:
        """Fetch all health insights for a patient"""
        return await self.health_insight_repository.get_by_patient_id(patient_id, limit=limit, skip=skip)

    async def update_insight(
        self,
        insight_id: str,
        schema: HealthInsightUpdateSchema,
    ) -> Optional[HealthInsightInDB]:
        """Update an existing health insight"""
        # If source_report_id is being updated, validate it
        if schema.source_report_id is not None:
            report = await self.report_repository.get(schema.source_report_id)
            if not report:
                raise ValueError(f"Source report with ID {schema.source_report_id} does not exist")

        update = HealthInsightUpdate(**schema.model_dump(exclude_unset=True))
        return await self.health_insight_repository.update(insight_id, update)

    async def delete_insight(self, insight_id: str) -> bool:
        """Permanently delete a health insight"""
        return await self.health_insight_repository.delete(insight_id)

    def to_response(self, insight: HealthInsightInDB) -> HealthInsightResponse:
        """Convert internal model to API response"""
        return _insight_to_response(insight)
