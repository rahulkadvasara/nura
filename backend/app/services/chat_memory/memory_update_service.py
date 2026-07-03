"""
Nura - Memory Update Service
Coordinates background Qdrant vector memory indexing and MongoDB patient memory structured updates
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

from app.models.patient_memory import (
    PatientMemoryUpdate,
    PatientMemoryCreate,
)
from app.repositories.patient_memory_repository import PatientMemoryRepository
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.services.chat_memory.conversation_evaluator import ConversationEvaluator
from app.services.chat_memory.conversation_summary_service import ConversationSummaryService
from app.services.chat_memory.telemetry import memory_telemetry

logger = logging.getLogger(__name__)


class MemoryUpdateService:
    """Orchestrates database write operations for chat intelligence memories"""

    def __init__(
        self,
        patient_memory_repository: PatientMemoryRepository,
        embedding_service: EmbeddingService,
        vector_service: VectorService,
        evaluator: ConversationEvaluator,
        summary_service: ConversationSummaryService,
    ):
        self.patient_memory_repository = patient_memory_repository
        self.embedding_service = embedding_service
        self.vector_service = vector_service
        self.evaluator = evaluator
        self.summary_service = summary_service

    async def evaluate_and_sync_session(
        self,
        session_id: str,
        patient_id: str,
        message_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Runs evaluation on a session. If worthiness scores cross thresholds, compiles
        an AI summary and updates Qdrant vector memory and MongoDB patient memory.
        """
        # 1. Evaluate conversation
        eval_result = await self.evaluator.evaluate_session(session_id)
        
        should_store_chat = eval_result["should_store_chat_memory"]
        should_store_patient = eval_result["should_update_patient_memory"]

        if not should_store_chat and not should_store_patient:
            logger.info(f"Session {session_id} skipped for memory sync (Score: {eval_result['memory_score']})")
            return {
                "success": True,
                "status": "skipped",
                "evaluation": eval_result
            }

        # 2. Get session messages
        from app.core.dependencies import get_chat_message_repository
        msg_repo = get_chat_message_repository()
        messages = await msg_repo.get_by_session_id(session_id, limit=100, skip=0, include_deleted=False)
        formatted_msgs = [
            {
                "role": m.role.value if hasattr(m.role, "value") else str(m.role),
                "content": m.content
            }
            for m in messages
        ]

        # 3. Generate summary content
        summary_data = await self.summary_service.generate_summary(formatted_msgs)
        summary_text = summary_data["summary"]
        keywords = summary_data["keywords"]
        entities = summary_data["entities"]

        # 4. Upsert Qdrant chat_memory if semantic value exists
        if should_store_chat:
            try:
                # Generate embedding
                embedding = await self.embedding_service.embed(summary_text)
                
                point_id = str(uuid.uuid4())
                payload = {
                    "patient_id": patient_id,
                    "session_id": session_id,
                    "summary": summary_text,
                    "keywords": keywords,
                    "entities": entities,
                    "message_ids": message_ids,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                # Idempotent collection verification
                await self.vector_service.create_collection("chat_memory")
                
                # Upsert point
                await self.vector_service.upsert(
                    collection_name="chat_memory",
                    id=point_id,
                    vector=embedding,
                    payload=payload
                )
                
                memory_telemetry.record_qdrant_update()
                logger.info(f"Upserted chat memory vector point for session {session_id} to Qdrant")
            except Exception as e:
                logger.error(f"Failed to upsert chat memory to Qdrant: {e}", exc_info=True)

        # 5. Append MongoDB patient_memory if clinical relevance is high
        if should_store_patient:
            try:
                existing = await self.patient_memory_repository.get_by_patient_id(patient_id)
                
                def append_unique(existing_list, new_items) -> List[str]:
                    curr = list(existing_list or [])
                    for item in new_items:
                        if item and str(item).strip() and str(item).strip().lower() not in [str(x).strip().lower() for x in curr]:
                            curr.append(str(item).strip())
                    return curr

                def append_history(existing_history, new_items, key_name) -> List[Dict[str, Any]]:
                    curr = list(existing_history or [])
                    for item in new_items:
                        exists = any(h.get(key_name) == item for h in curr)
                        if not exists:
                            curr.append({
                                key_name: item,
                                "report_date": datetime.now(timezone.utc).isoformat(),
                                "source": "conversation"
                            })
                    return curr

                # Safe list extractions
                medications = summary_data.get("medications", [])
                symptoms = summary_data.get("symptoms", [])
                diagnoses = summary_data.get("diagnoses", [])
                recommendations = summary_data.get("recommendations", [])
                followups = summary_data.get("followups", [])

                if existing:
                    # Update (Incremental Append)
                    update_payload = PatientMemoryUpdate(
                        medications=append_unique(existing.medications, medications),
                        allergies=existing.allergies, # No updates in summary format directly
                        diagnoses=append_unique(existing.diagnoses, diagnoses),
                        recent_findings=append_unique(existing.recent_findings, symptoms),
                        lifestyle_notes=f"{existing.lifestyle_notes}\n{'; '.join(recommendations)}" if existing.lifestyle_notes else "; ".join(recommendations),
                        medication_history=append_history(existing.medication_history, medications, "medicine"),
                        diagnosis_history=append_history(existing.diagnosis_history, diagnoses, "diagnosis")
                    )
                    await self.patient_memory_repository.update(existing.id, update_payload)
                else:
                    # Create baseline memory
                    create_payload = PatientMemoryCreate(
                        patient_id=patient_id,
                        medications=medications,
                        allergies=[],
                        diagnoses=diagnoses,
                        recent_findings=symptoms,
                        lifestyle_notes="; ".join(recommendations),
                        timeline=[{
                            "type": "conversation_memory",
                            "description": "Conversation Memory Sync initialized",
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }],
                        medication_history=[{
                            "medicine": m,
                            "report_date": datetime.now(timezone.utc).isoformat(),
                            "source": "conversation"
                        } for m in medications],
                        diagnosis_history=[{
                            "diagnosis": d,
                            "report_date": datetime.now(timezone.utc).isoformat(),
                            "source": "conversation"
                        } for d in diagnoses]
                    )
                    await self.patient_memory_repository.create(create_payload)

                memory_telemetry.record_patient_memory_update()
                logger.info(f"Updated MongoDB patient memory record for patient {patient_id}")
            except Exception as e:
                logger.error(f"Failed to update MongoDB patient memory: {e}", exc_info=True)

        return {
            "success": True,
            "status": "stored",
            "evaluation": eval_result,
            "summary": summary_text,
            "keywords": keywords,
            "entities": entities
        }
