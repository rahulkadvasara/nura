import logging
from typing import Dict, Any, List
from app.repositories.report_repository import ReportRepository
from app.repositories.patient_memory_repository import PatientMemoryRepository

logger = logging.getLogger("nura.report_pipeline.validator")


class PipelineValidator:
    """Audits report status, database schema matches, memory indexes, and vector points consistency"""

    def __init__(
        self,
        report_repository: ReportRepository,
        patient_memory_repository: PatientMemoryRepository,
        vector_service=None
    ):
        self.report_repository = report_repository
        self.patient_memory_repository = patient_memory_repository
        self.vector_service = vector_service

    async def validate_report_readiness(self, report_id: str) -> Dict[str, Any]:
        """Perform indexing sanity audits and cross-check Qdrant/MongoDB counts"""
        report = await self.report_repository.get(report_id)
        if not report:
            return {
                "valid": False,
                "issues": [f"Report with ID {report_id} was not found"],
                "report_status": "NOT_FOUND",
                "qdrant_chunks_count": 0,
                "patient_id": ""
            }

        issues = []

        # Validate extraction output presence
        if (
            not getattr(report, "laboratory_results", None)
            and not getattr(report, "medications", None)
            and not getattr(report, "diagnoses", None)
        ):
            issues.append("Extracted clinical parameters are missing")

        # Validate risk analysis output presence
        if not getattr(report, "overall_risk", None):
            issues.append("Risk analysis parameters are missing")

        # Validate summary details presence
        if not getattr(report, "ai_summary", None) and not getattr(report, "patient_summary", None):
            issues.append("AI summary descriptions are missing")

        # Validate sync flags
        if not getattr(report, "is_synchronized", False):
            issues.append("Report is not marked as synchronized")

        # Verify MongoDB Patient Memory
        memory = await self.patient_memory_repository.get_by_patient_id(report.patient_id)
        if not memory:
            issues.append("Longitudinal patient memory document is missing in MongoDB")
        else:
            has_summary = any(
                s.get("report_id") == report_id
                for s in getattr(memory, "report_summaries", []) or []
            )
            if not has_summary:
                issues.append("Report summary is missing from longitudinal memory logs")

        # Verify Qdrant points count
        qdrant_count = 0
        if self.vector_service:
            try:
                # Query vector store points matching this report ID
                from qdrant_client.http import models as rest_models
                query_filter = rest_models.Filter(
                    must=[
                        rest_models.FieldCondition(
                            key="report_id",
                            match=rest_models.MatchValue(value=report_id)
                        )
                    ]
                )
                points, _ = await self.vector_service.scroll(
                    collection_name="patient_reports",
                    scroll_filter=query_filter,
                    limit=100
                )
                qdrant_count = len(points)
                if qdrant_count == 0:
                    issues.append("No vector chunks found in Qdrant collection")
            except Exception as e:
                logger.error(f"Failed to scroll Qdrant points during validation of {report_id}: {e}")
                issues.append(f"Qdrant connection error: {str(e)}")

        is_valid = len(issues) == 0
        return {
            "valid": is_valid,
            "issues": issues,
            "report_status": getattr(report, "processing_status", "unknown"),
            "qdrant_chunks_count": qdrant_count,
            "patient_id": report.patient_id
        }
