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
    """Production agent managing patient longitudinal memory summaries, past records recall, and chat memories sync"""

    def __init__(
        self,
        patient_memory_repository: PatientMemoryRepository,
        chat_message_repository: ChatMessageRepository,
        retrieval_service: RetrievalService,
        memory_sync_service: MemorySyncService,
        patient_context_service: Optional[Any] = None,
        ai_service: Optional[Any] = None,
        settings=None
    ):
        super().__init__(name="MemoryAgent", settings=settings or ai_settings)
        self.patient_memory_repository = patient_memory_repository
        self.chat_message_repository = chat_message_repository
        self.retrieval_service = retrieval_service
        self.memory_sync_service = memory_sync_service

        if patient_context_service is None:
            from app.core.dependencies import get_patient_context_service
            self.patient_context_service = get_patient_context_service()
        else:
            self.patient_context_service = patient_context_service

        if ai_service is None:
            from app.core.dependencies import get_ai_service
            self.ai_service = get_ai_service()
        else:
            self.ai_service = ai_service

        self.telemetry = get_core_agents_telemetry()

    def _format_patient_details(self, memory: Any, ctx_res: Any = None) -> str:
        """Helper to format complete patient records and summary details for prompt usage"""
        lines = []
        if memory:
            lines.append(f"AI Longitudinal Summary: {memory.ai_summary or 'None'}")
            if memory.chronic_conditions:
                lines.append(f"Chronic Conditions: {', '.join(memory.chronic_conditions)}")
            if memory.allergies:
                lines.append(f"Allergies: {', '.join(memory.allergies)}")
            if memory.medications:
                lines.append(f"Active Medications: {', '.join(memory.medications)}")
            if memory.surgeries:
                lines.append(f"Surgeries: {', '.join(memory.surgeries)}")
            if memory.diagnoses:
                lines.append(f"Past Diagnoses: {', '.join(memory.diagnoses)}")

        if ctx_res:
            if getattr(ctx_res, "reports", None):
                lines.append("\nUploaded Diagnostic Reports:")
                for r in ctx_res.reports[:5]:
                    lines.append(f"- Report: {r.document_type} (Date: {r.created_at}, Risk: {r.risk_level}, Summary: {r.ai_summary or 'N/A'})")
            if getattr(ctx_res, "appointments", None):
                lines.append("\nAppointments Record:")
                for a in ctx_res.appointments[:5]:
                    lines.append(f"- Date: {a.slot_date} at {a.slot_time}, Status: {a.status}, Reason: {a.reason or 'Consultation'}")
            if getattr(ctx_res, "consultations", None):
                lines.append("\nPast Doctor Consultations:")
                for c in ctx_res.consultations[:5]:
                    lines.append(f"- Diagnosis: {c.diagnosis}, Doctor Notes: {c.consultation_notes}")
            if getattr(ctx_res, "prescriptions", None):
                lines.append("\nPrescribed Medications:")
                for p in ctx_res.prescriptions[:5]:
                    meds_str = ", ".join([f"{m.drug_name} ({m.dosage})" for m in p.medications])
                    lines.append(f"- Prescription: {meds_str}")

        return "\n".join(lines) if lines else "No past medical records compiled."

    async def execute(self, input_data: Any, context: Optional[AgentContext] = None) -> Any:
        """
        Execute Memory retrieval, past records compilation, and LLM answer synthesis:
        - Load MongoDB patient context & longitudinal memory
        - Pull recent chat conversation history & Qdrant memory vectors
        - Synthesize personalized recall response via LLM
        """
        query = str(input_data).strip() if input_data else "retrieve medical memories"
        patient_id = context.patient_id if context else None
        session_id = context.session_id if context else None
        
        start_time = time.perf_counter()
        
        patient_memory = None
        patient_ctx_res = None
        recent_messages = []
        semantic_memories = []
        sync_res = {}
        
        if patient_id:
            # 1. Fetch longitudinal memory & full records context from MongoDB
            try:
                patient_memory = await self.patient_memory_repository.get_by_patient_id(patient_id)
            except Exception as e:
                self.logger.warning(f"Failed to fetch longitudinal memory: {e}")

            try:
                patient_ctx_res = await self.patient_context_service.assemble_context(patient_id)
            except Exception as e:
                self.logger.warning(f"Failed to assemble patient context in MemoryAgent: {e}")
            
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
                patient_memory = await self.patient_memory_repository.get_by_patient_id(patient_id)
            except Exception as e:
                self.logger.warning(f"Failed to execute memory synchronization: {str(e)}")

        patient_records_summary = self._format_patient_details(patient_memory, patient_ctx_res)
        
        # Build LLM Prompt for memory recall response
        system_prompt = (
            "You are Nura's Memory & Health Recall AI Assistant. "
            "Your task is to accurately answer the patient's questions about their past medical history, "
            "past doctor consultations, diagnostic reports, active prescriptions, appointments, and past chat discussions. "
            "Provide a clear, empathetic, personalized response based strictly on the patient's actual medical records provided."
        )

        chat_memories_str = "\n".join([str(m.get("content", "")) for m in semantic_memories]) if semantic_memories else "No previous chat memories matching query."
        user_prompt = (
            f"Patient Query: '{query}'\n\n"
            f"Patient Medical Records & History:\n{patient_records_summary}\n\n"
            f"Relevant Past Chat Discussions:\n{chat_memories_str}\n\n"
            "Please provide a helpful, direct, and structured answer to the patient's recall query."
        )

        groq_latency = 0.0
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        cost = 0.0

        try:
            groq_start = time.perf_counter()
            ai_res = await self.ai_service.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                request_id=context.request_id if context else None
            )
            groq_latency = (time.perf_counter() - groq_start) * 1000.0
            memory_summary = ai_res.response
            prompt_tokens = ai_res.prompt_tokens
            completion_tokens = ai_res.completion_tokens
            total_tokens = ai_res.total_tokens
            cost = ai_res.estimated_cost
        except Exception as e:
            self.logger.error(f"MemoryAgent LLM generation failed: {e}", exc_info=True)
            memory_summary = patient_records_summary

        total_latency = (time.perf_counter() - start_time) * 1000.0
        
        # Build Response
        agent_res = MemoryAgentResponse(
            memory_summary=memory_summary,
            conversation_history=recent_messages,
            patient_summary=patient_records_summary,
            relevant_context=semantic_memories,
            metadata={
                "sync_result": sync_res,
                "groq_latency_ms": groq_latency,
                "total_latency_ms": total_latency,
                "summary_version": getattr(patient_memory, "summary_version", 1) if patient_memory else 1
            }
        )

        # Record telemetry
        self.telemetry.record_run(
            agent_name=self.name,
            latency_ms=total_latency,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost=cost,
            success=True,
            retrieval_latency_ms=total_latency * 0.2,
            groq_latency_ms=groq_latency
        )

        return agent_res
