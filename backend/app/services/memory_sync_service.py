"""
Nura - Patient Memory Synchronization Service
Coordinates the incremental synchronization of patient memory records from MongoDB to Qdrant
"""

import time
import logging
import json
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from app.models.patient_memory import PatientMemoryCreate, PatientMemoryUpdate, PatientMemoryInDB
from app.repositories.patient_memory_repository import PatientMemoryRepository
from app.repositories.user_repository import UserRepository
from app.services.patient_summary_builder import PatientSummaryBuilder
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.services.index_version_service import IndexVersionService
from app.services.audit_log_service import AuditLogService
from app.utils.ai import memory_sync_metrics
from app.schemas.observability import AuditLogCreateSchema
from app.models.user import UserRole
from app.events.base import BaseEvent

logger = logging.getLogger("nura.services.memory_sync_service")


class MemorySyncService:
    """Coordinated synchronization of patient summaries from MongoDB to Qdrant"""

    def __init__(
        self,
        patient_memory_repository: PatientMemoryRepository,
        user_repository: UserRepository,
        patient_summary_builder: PatientSummaryBuilder,
        embedding_service: EmbeddingService,
        vector_service: VectorService,
        index_version_service: IndexVersionService,
        audit_log_service: AuditLogService,
    ):
        self.patient_memory_repository = patient_memory_repository
        self.user_repository = user_repository
        self.patient_summary_builder = patient_summary_builder
        self.embedding_service = embedding_service
        self.vector_service = vector_service
        self.index_version_service = index_version_service
        self.audit_log_service = audit_log_service

    def calculate_summary_hash(self, summary: PatientMemoryCreate) -> str:
        """Deterministically calculate MD5 content hash for a patient memory record"""
        data = {
            "ai_summary": summary.ai_summary or "",
            "chronic_conditions": sorted(summary.chronic_conditions),
            "allergies": sorted(summary.allergies),
            "medications": sorted(summary.medications),
            "surgeries": sorted(summary.surgeries),
            "diagnoses": sorted(summary.diagnoses),
            "health_risks": sorted(summary.health_risks),
            "recent_findings": summary.recent_findings,
            "lifestyle_notes": summary.lifestyle_notes or "",
            "timeline": summary.timeline
        }
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(serialized.encode("utf-8")).hexdigest()

    def chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """Split summary text into small, readable semantic chunks"""
        if not text:
            return []
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_with_dot = sentence + "."
            if current_length + len(sentence_with_dot) > chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentence_with_dot]
                current_length = len(sentence_with_dot)
            else:
                current_chunk.append(sentence_with_dot)
                current_length += len(sentence_with_dot)
                
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        return chunks

    async def sync_patient(self, patient_id: str, event: Optional[BaseEvent] = None) -> Dict[str, Any]:
        """
        Executes longitudinal patient summary synchronization flow:
        - Compiles updated data from MongoDB collections
        - Compares the content hash for changes
        - Saves to MongoDB (with version increment)
        - Vectorizes and upserts to Qdrant (recovering if index is out of sync)
        - Verifies the state of both databases
        """
        start_time = time.perf_counter()
        logger.info(f"Starting synchronization pipeline for patient {patient_id}")

        try:
            # 1. Fetch existing patient memory
            existing_memory = await self.patient_memory_repository.get_by_patient_id(patient_id)

            # 2. Build new patient memory summary
            new_summary = await self.patient_summary_builder.build_summary(patient_id)
            new_hash = self.calculate_summary_hash(new_summary)

            # 3. Check for structural or content changes
            content_changed = (existing_memory is None) or (existing_memory.content_hash != new_hash)

            # 4. Check Qdrant state to detect if we are out of sync/missing records
            qdrant_points, _ = await self.vector_service.scroll(
                collection_name="patient_memory",
                filter_dict={"patient_id": patient_id},
                limit=100
            )

            current_embedding_version = self.index_version_service.get_embedding_version()
            current_schema_version = self.index_version_service.get_schema_version()
            current_summary_version = (existing_memory.summary_version) if existing_memory else 1

            in_sync = (len(qdrant_points) > 0)
            if in_sync:
                for p in qdrant_points:
                    meta = p.get("payload", {})
                    # Ensure compatibility and version matching
                    if (
                        meta.get("summary_version") != current_summary_version or
                        meta.get("embedding_version") != current_embedding_version or
                        meta.get("schema_version") != current_schema_version
                    ):
                        in_sync = False
                        break

            # 5. Incremental index update or skip
            rebuilt_mongodb = False
            regenerated_qdrant = False

            if content_changed:
                logger.info(f"Content changed or first sync for patient {patient_id}. Updating records.")
                # Increment summary version
                summary_version = (existing_memory.summary_version + 1) if existing_memory else 1
                new_summary.summary_version = summary_version
                new_summary.content_hash = new_hash

                # Save updated memory to MongoDB
                if existing_memory:
                    # Update existing record
                    update_payload = PatientMemoryUpdate(**new_summary.model_dump())
                    updated_record = await self.patient_memory_repository.update(existing_memory.id, update_payload)
                    if not updated_record:
                        raise RuntimeError(f"Failed to update patient memory record for patient {patient_id}")
                else:
                    # Create new record
                    await self.patient_memory_repository.create(new_summary)
                
                rebuilt_mongodb = True
                
                # Delete existing Qdrant points and force vector regeneration
                await self.vector_service.delete_by_filter(
                    collection_name="patient_memory",
                    filter_dict={"patient_id": patient_id}
                )

                # Generate new vector points in Qdrant
                chunks = self.chunk_text(new_summary.ai_summary)
                if chunks:
                    embedding_results = await self.embedding_service.embed_batch(
                        texts=chunks,
                        document_type="patient_memory",
                        source_id=patient_id,
                        collection_target="patient_memory",
                        patient_id=patient_id
                    )

                    qdrant_points = [
                        {
                            "id": str(uuid.uuid4()),
                            "vector": res.vector,
                            "payload": {
                                "patient_id": patient_id,
                                "text": res.text,
                                "summary_version": summary_version,
                                "embedding_version": current_embedding_version,
                                "schema_version": current_schema_version,
                                "indexed_at": datetime.now(timezone.utc).isoformat()
                            }
                        }
                        for res in embedding_results
                    ]

                    await self.vector_service.upsert_batch("patient_memory", qdrant_points)
                    regenerated_qdrant = True
                    logger.info(f"Upserted {len(qdrant_points)} vector points to Qdrant for patient {patient_id}")

            elif not in_sync:
                logger.info(f"Content unchanged but Qdrant index is out of sync for patient {patient_id}. Re-indexing.")
                
                # Re-index existing MongoDB summary to Qdrant
                await self.vector_service.delete_by_filter(
                    collection_name="patient_memory",
                    filter_dict={"patient_id": patient_id}
                )

                chunks = self.chunk_text(existing_memory.ai_summary)
                if chunks:
                    embedding_results = await self.embedding_service.embed_batch(
                        texts=chunks,
                        document_type="patient_memory",
                        source_id=patient_id,
                        collection_target="patient_memory",
                        patient_id=patient_id
                    )

                    qdrant_points = [
                        {
                            "id": str(uuid.uuid4()),
                            "vector": res.vector,
                            "payload": {
                                "patient_id": patient_id,
                                "text": res.text,
                                "summary_version": current_summary_version,
                                "embedding_version": current_embedding_version,
                                "schema_version": current_schema_version,
                                "indexed_at": datetime.now(timezone.utc).isoformat()
                            }
                        }
                        for res in embedding_results
                    ]

                    await self.vector_service.upsert_batch("patient_memory", qdrant_points)
                    regenerated_qdrant = True
                    logger.info(f"Repaired and upserted {len(qdrant_points)} vector points to Qdrant for patient {patient_id}")
            else:
                logger.info(f"Patient memory for {patient_id} is already in-sync. Skipping vector update.")

            # 6. Verification check
            verified_points, _ = await self.vector_service.scroll(
                collection_name="patient_memory",
                filter_dict={"patient_id": patient_id},
                limit=100
            )

            expected_version = summary_version if content_changed else current_summary_version
            # If there was summary text, we expect some chunks in Qdrant
            summary_to_check = new_summary.ai_summary if content_changed else (existing_memory.ai_summary if existing_memory else None)
            expected_chunks = len(self.chunk_text(summary_to_check)) if summary_to_check else 0

            if expected_chunks > 0 and len(verified_points) == 0:
                raise ValueError(f"Post-sync verification failed: Expected {expected_chunks} chunks but found 0 points in Qdrant")

            for pt in verified_points:
                pt_ver = pt.get("payload", {}).get("summary_version")
                if pt_ver != expected_version:
                    raise ValueError(f"Post-sync verification failed: Qdrant point version {pt_ver} does not match expected {expected_version}")

            # 7. Audit Logging on change success
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            
            if rebuilt_mongodb or regenerated_qdrant:
                # Store audit trail
                await self.audit_log_service.create_log(
                    AuditLogCreateSchema(
                        user_id=None,  # system trigger
                        action="PATIENT_RAG_SYNC",
                        resource_type="patient_memory",
                        resource_id=patient_id,
                        new_value={
                            "summary_version": expected_version,
                            "content_hash": new_hash if content_changed else existing_memory.content_hash,
                            "rebuilt_mongodb": rebuilt_mongodb,
                            "regenerated_qdrant": regenerated_qdrant,
                            "latency_ms": latency_ms
                        }
                    )
                )

            # Record telemetry metrics
            memory_sync_metrics.record_sync(
                latency_ms=latency_ms,
                rebuilt=rebuilt_mongodb,
                regenerated=regenerated_qdrant
            )

            return {
                "success": True,
                "patient_id": patient_id,
                "rebuilt_mongodb": rebuilt_mongodb,
                "regenerated_qdrant": regenerated_qdrant,
                "summary_version": expected_version,
                "latency_ms": latency_ms
            }

        except Exception as e:
            logger.error(f"Error executing sync for patient {patient_id}: {str(e)}", exc_info=True)
            # Metrics failure
            memory_sync_metrics.record_failure()
            raise e

    async def sync_all_patients(self) -> Dict[str, Any]:
        """
        Manually triggers a full synchronization loop for all active patient accounts.
        Runs by dispatching event updates sequentially through the background EventQueue.
        """
        try:
            # Query UserRepository directly for all patient IDs
            patient_users = await self.user_repository.get_many(
                filter_dict={"role": UserRole.PATIENT.value},
                limit=1000
            )
            
            patient_ids = [u.id for u in patient_users]
            logger.info(f"Triggering full synchronization rebuild for {len(patient_ids)} patients")

            from app.events.base import PatientProfileUpdatedEvent
            from app.core.dependencies import get_event_dispatcher
            dispatcher = get_event_dispatcher()

            count = 0
            for pid in patient_ids:
                # Dispatch event to invoke the queue consumer in the background
                event = PatientProfileUpdatedEvent(patient_id=pid)
                await dispatcher.dispatch(event)
                count += 1

            return {
                "success": True,
                "triggered_count": count,
                "patient_ids": patient_ids
            }
        except Exception as e:
            logger.error(f"Failed to sync all patients: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
