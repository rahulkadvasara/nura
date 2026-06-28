"""
Nura - Clinical Report Synchronization Validator
"""

import logging
from typing import Dict, Any, List
from app.repositories.report_repository import ReportRepository
from app.repositories.patient_memory_repository import PatientMemoryRepository
from app.services.vector_service import VectorService
from app.services.index_version_service import IndexVersionService
from app.services.report_sync.chunk_builder import ReportChunkBuilder

logger = logging.getLogger("nura.report_sync.sync_validator")


class ReportSyncValidator:
    """Validates the state consistency across patient_memory (MongoDB) and patient_reports (Qdrant)"""

    def __init__(
        self,
        report_repository: ReportRepository,
        patient_memory_repository: PatientMemoryRepository,
        vector_service: VectorService,
        index_version_service: IndexVersionService,
        chunk_builder: ReportChunkBuilder
    ):
        self.report_repository = report_repository
        self.patient_memory_repository = patient_memory_repository
        self.vector_service = vector_service
        self.index_version_service = index_version_service
        self.chunk_builder = chunk_builder

    async def validate_synchronization(self, report_id: str) -> Dict[str, Any]:
        """Audits both database states for a given medical report"""
        report = await self.report_repository.get(report_id)
        if not report:
            return {
                "in_sync": False,
                "error": f"Report {report_id} does not exist in MongoDB"
            }

        patient_id = report.patient_id

        # 1. Inspect MongoDB patient_memory
        memory = await self.patient_memory_repository.get_by_patient_id(patient_id)
        mongodb_valid = False
        mongodb_status = "missing"
        
        if memory:
            mongodb_status = "present"
            # Ensure latest summary and risks match the report details
            if memory.latest_report_summary == report.ai_summary:
                mongodb_valid = True
            else:
                mongodb_status = "summary_mismatch"

        # 2. Inspect Qdrant patient_reports vectors
        qdrant_points, _ = await self.vector_service.scroll(
            collection_name="patient_reports",
            filter_dict={"report_id": report_id},
            limit=100
        )

        expected_chunks = self.chunk_builder.build_report_chunks(report)
        qdrant_valid = len(qdrant_points) > 0 and len(qdrant_points) == len(expected_chunks)
        qdrant_status = f"found_{len(qdrant_points)}_of_{len(expected_chunks)}_expected"

        current_emb_version = self.index_version_service.get_embedding_version()

        metadata_preserved = True
        duplicate_chunks = False
        version_synchronized = True
        checked_texts = set()

        for pt in qdrant_points:
            meta = pt.get("payload", {})
            # Verify metadata properties
            if (
                meta.get("patient_id") != patient_id or
                meta.get("report_id") != report_id or
                "document_type" not in meta or
                "report_date" not in meta or
                "section" not in meta
            ):
                metadata_preserved = False

            # Verify embedding version compatibility
            if meta.get("embedding_version") != current_emb_version:
                version_synchronized = False

            # Check duplicate text chunks
            text = meta.get("text")
            if text in checked_texts:
                duplicate_chunks = True
            checked_texts.add(text)

        in_sync = mongodb_valid and qdrant_valid and metadata_preserved and not duplicate_chunks and version_synchronized

        return {
            "in_sync": in_sync,
            "report_id": report_id,
            "patient_id": patient_id,
            "validation_details": {
                "mongodb_memory_status": mongodb_status,
                "mongodb_valid": mongodb_valid,
                "qdrant_points_status": qdrant_status,
                "qdrant_valid": qdrant_valid,
                "metadata_preserved": metadata_preserved,
                "duplicate_chunks_detected": duplicate_chunks,
                "version_synchronized": version_synchronized,
                "embedding_version": current_emb_version
            }
        }
