"""
Nura - Clinical Report Knowledge Synchronization Service
"""

import time
import uuid
import logging
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from app.models.report import ReportInDB
from app.repositories.report_repository import ReportRepository
from app.repositories.patient_memory_repository import PatientMemoryRepository
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.services.index_version_service import IndexVersionService
from app.services.audit_log_service import AuditLogService
from app.services.report_sync.patient_memory_builder import ReportPatientMemoryBuilder
from app.services.report_sync.chunk_builder import ReportChunkBuilder
from app.services.report_sync.telemetry import get_report_sync_telemetry
from app.models.patient_memory import PatientMemoryUpdate
from app.schemas.observability import AuditLogCreateSchema

logger = logging.getLogger("nura.report_sync.report_sync_service")


class ReportSyncService:
    """Coordinates patient report summarization and synchronization to patient_memory and Qdrant"""

    def __init__(
        self,
        report_repository: ReportRepository,
        patient_memory_repository: PatientMemoryRepository,
        memory_builder: ReportPatientMemoryBuilder,
        chunk_builder: ReportChunkBuilder,
        embedding_service: EmbeddingService,
        vector_service: VectorService,
        index_version_service: IndexVersionService,
        audit_log_service: AuditLogService
    ):
        self.report_repository = report_repository
        self.patient_memory_repository = patient_memory_repository
        self.memory_builder = memory_builder
        self.chunk_builder = chunk_builder
        self.embedding_service = embedding_service
        self.vector_service = vector_service
        self.index_version_service = index_version_service
        self.audit_log_service = audit_log_service

    def calculate_chunks_hash(self, chunks: List[Dict[str, Any]]) -> str:
        """Calculate content hash for report chunks list"""
        texts = [c["text"] for c in chunks]
        serialized = json.dumps(sorted(texts))
        return hashlib.md5(serialized.encode("utf-8")).hexdigest()

    async def synchronize_report(self, report_id: str) -> Dict[str, Any]:
        """Runs the medical report synchronization pipeline:
        - Updates patient_memory MongoDB collection
        - Formulates semantic sentence chunks
        - Generates vector embeddings and upserts to Qdrant patient_reports
        - Validates synchronization states
        """
        start_time = time.perf_counter()
        logger.info(f"Triggering report sync pipeline for report {report_id}")

        try:
            # 1. Fetch Report
            report = await self.report_repository.get(report_id)
            if not report:
                raise ValueError(f"Report {report_id} not found in database")

            patient_id = report.patient_id
            
            # Ensure report is sufficiently processed to permit sync
            if report.processing_status != "completed":
                raise ValueError(f"Report {report_id} status is {report.processing_status}. Must be 'completed' to synchronize.")

            # 2. Update patient_memory in MongoDB
            updated_mem = await self.memory_builder.build_incremental_memory(patient_id, report)
            existing_mem = await self.patient_memory_repository.get_by_patient_id(patient_id)
            
            if existing_mem:
                # Increment version
                updated_mem.summary_version = existing_mem.summary_version + 1
                payload = PatientMemoryUpdate(**updated_mem.model_dump())
                await self.patient_memory_repository.update(existing_mem.id, payload)
            else:
                updated_mem.summary_version = 1
                await self.patient_memory_repository.create(updated_mem)

            # 2.5 Medication Validation Integration
            try:
                from app.core.dependencies import get_medication_validation_service
                validation_service = get_medication_validation_service()
                
                # Extract raw medication names from the report
                report_meds = [
                    med.get("drug_name") or med.get("medicine")
                    for med in getattr(report, "medications", []) or []
                    if med.get("drug_name") or med.get("medicine")
                ]
                
                if report_meds:
                    val_res = await validation_service.validate_medications(
                        patient_id=patient_id,
                        incoming_medications=report_meds,
                        source="report"
                    )
                    
                    # Store interaction findings on the report document
                    findings = []
                    for inter in val_res.get("detected_interactions", []):
                        findings.append({
                            "drug_a": inter.drug_a,
                            "drug_b": inter.drug_b,
                            "drug_a_normalized": inter.drug_a_normalized,
                            "drug_b_normalized": inter.drug_b_normalized,
                            "severity": inter.severity,
                            "description": inter.description
                        })
                    
                    # Save interaction findings directly to the report document
                    await self.report_repository.collection.update_one(
                        {"_id": self.report_repository.collection.find_one({"_id": report_id}) or report_id},
                        {"$set": {"interaction_findings": findings}}
                    )

                # Re-evaluate the patient's full active list and update validation_summary inside patient_memory
                await validation_service.validate_and_update_patient_memory(patient_id)

            except Exception as validation_err:
                logger.error(f"Error executing medication safety validation during report sync for report {report_id}: {validation_err}")


            # 3. Build optimized semantic report chunks
            chunks = self.chunk_builder.build_report_chunks(report)
            content_hash = self.calculate_chunks_hash(chunks)

            # Check if this content is already fully indexed in Qdrant
            qdrant_points, _ = await self.vector_service.scroll(
                collection_name="patient_reports",
                filter_dict={"report_id": report_id},
                limit=100
            )

            current_emb_version = self.index_version_service.get_embedding_version()
            in_sync = len(qdrant_points) > 0 and len(qdrant_points) == len(chunks)
            if in_sync:
                for pt in qdrant_points:
                    meta = pt.get("payload", {})
                    if (
                        meta.get("content_hash") != content_hash or
                        meta.get("embedding_version") != current_emb_version
                    ):
                        in_sync = False
                        break

            # 4. Synchronize Qdrant (rebuild/upsert if out of sync)
            upserted_count = 0
            if not in_sync:
                # Delete existing report chunks vectors
                await self.vector_service.delete_by_filter(
                    collection_name="patient_reports",
                    filter_dict={"report_id": report_id}
                )

                # Embed and save new points
                if chunks:
                    texts_list = [c["text"] for c in chunks]
                    embedding_results = await self.embedding_service.embed_batch(
                        texts=texts_list,
                        document_type="patient_reports",
                        source_id=report_id,
                        collection_target="patient_reports",
                        patient_id=patient_id
                    )

                    report_date = report.created_at or datetime.now(timezone.utc)
                    report_date_str = report_date.isoformat() if isinstance(report_date, datetime) else str(report_date)

                    qdrant_points = [
                        {
                            "id": str(uuid.uuid4()),
                            "vector": emb.vector,
                            "payload": {
                                "patient_id": patient_id,
                                "report_id": report_id,
                                "document_type": report.document_type or "unknown",
                                "report_date": report_date_str,
                                "section": chunks[idx]["section"],
                                "source": "patient_reports",
                                "indexed_at": datetime.now(timezone.utc).isoformat(),
                                "embedding_version": current_emb_version,
                                "content_hash": content_hash,
                                "text": emb.text
                            }
                        }
                        for idx, emb in enumerate(embedding_results)
                    ]

                    await self.vector_service.upsert_batch("patient_reports", qdrant_points)
                    upserted_count = len(qdrant_points)
                    logger.info(f"Synchronized {upserted_count} vectors to Qdrant patient_reports for report {report_id}")

            # 5. Save sync completion state on the report document
            await self.report_repository.collection.update_one(
                {"_id": self.report_repository.collection.find_one({"_id": report_id}) or report_id},
                {"$set": {
                    "is_synchronized": True,
                    "synchronized_at": datetime.now(timezone.utc)
                }}
            )

            latency_ms = (time.perf_counter() - start_time) * 1000.0

            # 6. Logging Audit trails
            await self.audit_log_service.create_log(
                AuditLogCreateSchema(
                    user_id=None,
                    action="REPORT_KNOWLEDGE_SYNC",
                    resource_type="reports",
                    resource_id=report_id,
                    new_value={
                        "patient_id": patient_id,
                        "chunks_count": len(chunks),
                        "upserted_count": upserted_count,
                        "content_hash": content_hash,
                        "latency_ms": latency_ms
                    }
                )
            )

            # Record telemetry metrics
            get_report_sync_telemetry().record_sync_run(
                latency_ms=latency_ms,
                chunks_count=len(chunks),
                upserted_count=upserted_count,
                success=True
            )

            return {
                "success": True,
                "report_id": report_id,
                "patient_id": patient_id,
                "chunks_count": len(chunks),
                "upserted_count": upserted_count,
                "content_hash": content_hash,
                "latency_ms": latency_ms
            }

        except Exception as e:
            logger.error(f"Error synchronizing report {report_id}: {e}", exc_info=True)
            get_report_sync_telemetry().record_sync_run(
                latency_ms=(time.perf_counter() - start_time) * 1000.0,
                chunks_count=0,
                upserted_count=0,
                success=False
            )
            raise e

    async def unsynchronize_report(self, report_id: str) -> bool:
        """Removes report vectors from Qdrant patient_reports and flags database status on deletion"""
        logger.info(f"Removing vectors for deleted report {report_id}")
        try:
            await self.vector_service.delete_by_filter(
                collection_name="patient_reports",
                filter_dict={"report_id": report_id}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to unsynchronize report {report_id}: {e}")
            return False

    async def rebuild_all_synchronizations(self) -> Dict[str, Any]:
        """Rebuilds the synchronization status for all fully completed medical reports"""
        try:
            reports = await self.report_repository.get_many(
                filter_dict={"processing_status": "completed"},
                limit=1000
            )
            logger.info(f"Triggering rebuild synchronization for {len(reports)} completed reports")

            successful = 0
            failed = 0
            failed_ids = []

            for rep in reports:
                try:
                    await self.synchronize_report(rep.id)
                    successful += 1
                except Exception as err:
                    logger.warning(f"Failed to rebuild sync for report {rep.id}: {err}")
                    failed += 1
                    failed_ids.append(rep.id)

            return {
                "success": True,
                "total_jobs": len(reports),
                "successful_jobs": successful,
                "failed_jobs": failed,
                "failed_report_ids": failed_ids
            }
        except Exception as e:
            logger.error(f"Rebuild synchronization failure: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
