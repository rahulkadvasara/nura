"""
Nura - Medical Knowledge Agent
Concrete AI Agent for answering grounded medical questions using RAG.
"""

import time
import logging
from typing import Any, Optional, Dict, List

from app.agents.base.base_agent import BaseAgent
from app.agents.base.context import AgentContext
from app.agents.base.response import AgentResponse
from app.agents.core.schemas import MedicalKnowledgeAgentResponse
from app.agents.core.prompts import render_core_prompt
from app.agents.core.telemetry import get_core_agents_telemetry
from app.core.ai_config import ai_settings
from app.services.ai_service import AIService
from app.services.patient_context_service import PatientContextService
from app.agents.retrieval_agent import RetrievalAgent


class MedicalKnowledgeAgent(BaseAgent):
    """Production agent answering grounded medical inquiries based on Qdrant search results"""

    def __init__(
        self,
        retrieval_agent: RetrievalAgent,
        patient_context_service: PatientContextService,
        ai_service: AIService,
        settings=None
    ):
        super().__init__(name="MedicalKnowledgeAgent", settings=settings or ai_settings)
        self.retrieval_agent = retrieval_agent
        self.patient_context_service = patient_context_service
        self.ai_service = ai_service
        self.telemetry = get_core_agents_telemetry()

    def _format_patient_context(self, context_res: Any) -> str:
        """Utility to serialize structured PatientContextResponse into prompt string"""
        if not context_res:
            return "No patient context available."
            
        parts = []
        if getattr(context_res, "patient_profile", None):
            p = context_res.patient_profile
            parts.append(f"Patient Name: {p.get('full_name', 'Patient')}")
            
        if getattr(context_res, "medical_summary", None):
            parts.append(f"Medical Summary: {context_res.medical_summary}")
            
        if getattr(context_res, "current_conditions", None):
            parts.append(f"Chronic Conditions: {', '.join(context_res.current_conditions)}")
            
        if getattr(context_res, "current_medications", None):
            parts.append(f"Current Medications: {', '.join(context_res.current_medications)}")
            
        if getattr(context_res, "medication_allergies", None):
            parts.append(f"Allergies: {', '.join(context_res.medication_allergies)}")
            
        if getattr(context_res, "past_medical_history", None):
            parts.append(f"Medical timeline: {', '.join(context_res.past_medical_history)}")
            
        return "\n".join(parts) if parts else "No patient context available."

    async def execute(self, input_data: Any, context: Optional[AgentContext] = None) -> Any:
        """
        Execute RAG Pipeline:
        - Query Qdrant via RetrievalAgent
        - Compile Patient Context via PatientContextService
        - Formulate & render Prompts
        - Query Groq via AIService
        - Log telemetry and cost estimates
        """
        query = str(input_data).strip()
        patient_id = context.patient_id if context else None
        
        start_time = time.perf_counter()
        retrieval_start = time.perf_counter()
        
        # 1. Execute Retrieval Agent Qdrant query
        retrieval_res = await self.retrieval_agent.run(query, context)
        retrieval_latency = (time.perf_counter() - retrieval_start) * 1000.0
        
        retrieval_data = retrieval_res.response or {}
        retrieved_context = retrieval_data.get("context", "")
        citations_raw = retrieval_data.get("retrieved_chunks", [])
        collections_used = retrieval_data.get("collections_used", [])
        
        # Format citations to output structure
        citations = []
        for c in citations_raw:
            citations.append({
                "source": c.get("metadata", {}).get("source", "medical_knowledge"),
                "text": c.get("text", "")[:200] + "...",
                "score": c.get("score", 0.0),
                "document_id": c.get("metadata", {}).get("document_id")
            })

        # 2. Compile Patient Context from MongoDB
        patient_context_str = "No patient context available."
        if patient_id:
            try:
                patient_context_res = await self.patient_context_service.assemble_context(patient_id)
                patient_context_str = self._format_patient_context(patient_context_res)
            except Exception as e:
                self.logger.warning(f"Failed to assemble patient context: {str(e)}")

        # 3. Formulate prompts
        try:
            rendered_system = render_core_prompt("medical_question_system", {}, is_system=True)
            rendered_user = render_core_prompt("medical_question_user", {
                "patient_context": patient_context_str,
                "retrieved_context": retrieved_context or "No clinical reference text retrieved.",
                "query": query
            })
        except Exception as e:
            self.logger.error(f"Failed to render templates: {str(e)}")
            # Fallback to local default strings
            rendered_system = "You are a clinical knowledge assistant for Nura. Ground your answers strictly in the provided medical knowledge."
            rendered_user = f"Context:\n{retrieved_context}\n\nPatient Info:\n{patient_context_str}\n\nQuestion: {query}"

        # 4. Invoke LLM via AIService
        groq_start = time.perf_counter()
        ai_res = await self.ai_service.generate(
            prompt=rendered_user,
            system_prompt=rendered_system,
            request_id=context.request_id if context else None
        )
        groq_latency = (time.perf_counter() - groq_start) * 1000.0
        
        total_latency = (time.perf_counter() - start_time) * 1000.0
        
        # Normalize response schema output details
        agent_res = MedicalKnowledgeAgentResponse(
            answer=ai_res.response,
            citations=citations,
            confidence=0.90 if citations else 0.70,
            sources=collections_used,
            metadata={
                "retrieval_latency_ms": retrieval_latency,
                "groq_latency_ms": groq_latency,
                "total_latency_ms": total_latency,
                "prompt_version": "1.0.0"
            },
            usage={
                "prompt_tokens": ai_res.prompt_tokens,
                "completion_tokens": ai_res.completion_tokens,
                "total_tokens": ai_res.total_tokens
            }
        )

        # 5. Record telemetry metrics
        self.telemetry.record_run(
            agent_name=self.name,
            latency_ms=total_latency,
            prompt_tokens=ai_res.prompt_tokens,
            completion_tokens=ai_res.completion_tokens,
            total_tokens=ai_res.total_tokens,
            estimated_cost=ai_res.estimated_cost,
            success=True,
            retrieval_latency_ms=retrieval_latency,
            groq_latency_ms=groq_latency
        )
        
        return agent_res
