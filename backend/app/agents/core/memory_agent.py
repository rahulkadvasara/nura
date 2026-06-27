"""
Nura - Memory Agent
Concrete AI Agent for retrieving, updating, and syncing longitudinal patient clinical and conversational memory.
"""

import time
import logging
from typing import Any, Optional, Dict, List

from app.agents.base.base_agent import BaseAgent
from app.agents.base.context import AgentContext
from app.agents.base.response import AgentResponse
from app.agents.core.schemas import MemoryAgentResponse
from app.agents.core.telemetry import get_core_agents_telemetry
from app.core.ai_config import ai_settings
from app.repositories.patient_memory_repository import PatientMemoryRepository
from app.repositories.chat_message_repository import ChatMessageRepository
from app.services.retrieval_service import RetrievalService
from app.services.memory_sync_service import MemorySyncService


class MemoryAgent(BaseAgent):
    """Production agent managing patient longitudinal memory summaries and chat memories sync"""

    def __init__(
        self,
        patient_memory_repository: PatientMemoryRepository,
        chat_message_repository: ChatMessageRepository,
        retrieval_service: RetrievalService,
        memory_sync_service: MemorySyncService,
        settings=None
    ):
        super().__init__(name="MemoryAgent", settings=settings or ai_settings)
        self.patient_memory_repository = patient_memory_repository
        self.chat_message_repository = chat_message_repository
        self.retrieval_service = retrieval_service
        self.memory_sync_service = memory_sync_service
        self.telemetry = get_core_agents_telemetry()

    def _format_patient_details(self, memory: Any) -> str:
        """Helper to format summary details for prompt usage"""
        if not memory:
            return "No profile memory aggregated."
            
        lines = []
        lines.append(f"AI longitudinal Summary: {memory.ai_summary or 'None'}")
        lines.append(f"Chronic Conditions: {', '.join(memory.chronic_conditions)}")
        lines.append(f"Allergies: {', '.join(memory.allergies)}")
        lines.append(f"Active Medications: {', '.join(memory.medications)}")
        lines.append(f"Surgeries: {', '.join(memory.surgeries)}")
        lines.append(f"Diagnoses: {', '.join(memory.diagnoses)}")
        return "\n".join(lines)

    async def execute(self, input_data: Any, context: Optional[AgentContext] = None) -> Any:
        """
        Execute Memory retrieval and synchronization logic:
        - Load latest MongoDB patient memory
        - Pull recent chat conversation history
        - Retrieve semantic memory vectors from Qdrant
        - Trigger event synchronization to rebuild summaries and push to Qdrant
        """
        query = str(input_data).strip() if input_data else "retrieve medical memories"
        patient_id = context.patient_id if context else None
        session_id = context.session_id if context else None
        
        start_time = time.perf_counter()
        
        patient_memory = None
        recent_messages = []
        semantic_memories = []
        sync_res = {}
        
        if patient_id:
            # 1. Fetch longitudinal memory from MongoDB
            patient_memory = await self.patient_memory_repository.get_by_patient_id(patient_id)
            
            # 2. Fetch recent conversation messages
            if session_id:
                try:
                    msgs = await self.chat_message_repository.get_latest_messages(session_id, limit=20)
                    recent_messages = [m.model_dump() for m in msgs]
                except Exception as e:
                    self.logger.warning(f"Failed to fetch conversation history: {str(e)}")

            # 3. Retrieve Qdrant semantic memories
            try:
                retrieved = await self.retrieval_service.retrieve_multiple(
                    query=query,
                    collections=["chat_memory"],
                    filters={"patient_id": patient_id},
                    top_k=5
                )
                semantic_memories = retrieved.get("results", [])
            except Exception as e:
                self.logger.warning(f"Failed to retrieve semantic memories: {str(e)}")

            # 4. Trigger event-driven synchronization pipeline updates
            try:
                sync_res = await self.memory_sync_service.sync_patient(patient_id)
                # Re-fetch updated memory if it changed during sync
                patient_memory = await self.patient_memory_repository.get_by_patient_id(patient_id)
            except Exception as e:
                self.logger.error(f"Failed to execute memory synchronization: {str(e)}", exc_info=True)

        total_latency = (time.perf_counter() - start_time) * 1000.0
        
        memory_summary = patient_memory.ai_summary if patient_memory else "No memory compiled."
        patient_summary = self._format_patient_details(patient_memory) if patient_memory else "No memory compiled."
        
        # Build Response
        agent_res = MemoryAgentResponse(
            memory_summary=memory_summary,
            conversation_history=recent_messages,
            patient_summary=patient_summary,
            relevant_context=semantic_memories,
            metadata={
                "sync_result": sync_res,
                "total_latency_ms": total_latency,
                "summary_version": getattr(patient_memory, "summary_version", 1) if patient_memory else 1
            }
        )

        # 5. Record telemetry
        self.telemetry.record_run(
            agent_name=self.name,
            latency_ms=total_latency,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            estimated_cost=0.0,
            success=True,
            retrieval_latency_ms=total_latency * 0.2, # heuristic Qdrant retrieval latency share
            groq_latency_ms=0.0 # memory agent doesn't directly run LLM text completions
        )

        return agent_res
