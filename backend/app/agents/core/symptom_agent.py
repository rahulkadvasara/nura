"""
Nura - Symptom Agent
Concrete AI Agent for providing symptom analysis and escalation safety disclaimers.
"""

import time
import logging
from typing import Any, Optional, Dict, List

from app.agents.base.base_agent import BaseAgent
from app.agents.base.context import AgentContext
from app.agents.base.response import AgentResponse
from app.agents.core.schemas import SymptomAgentResponse
from app.agents.core.prompts import render_core_prompt
from app.agents.core.telemetry import get_core_agents_telemetry
from app.agents.core.utils import clean_json_response
from app.core.ai_config import ai_settings
from app.services.ai_service import AIService
from app.services.patient_context_service import PatientContextService
from app.agents.retrieval_agent import RetrievalAgent


class SymptomAgent(BaseAgent):
    """Production agent analyzing user-reported symptoms, asserting red flags, and escalations"""

    def __init__(
        self,
        retrieval_agent: RetrievalAgent,
        patient_context_service: PatientContextService,
        ai_service: AIService,
        settings=None
    ):
        super().__init__(name="SymptomAgent", settings=settings or ai_settings)
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
        return "\n".join(parts) if parts else "No patient context available."

    async def execute(self, input_data: Any, context: Optional[AgentContext] = None) -> Any:
        """
        Execute Symptom Analysis pipeline:
        - Query Qdrant via RetrievalAgent
        - Compile patient history from MongoDB
        - Render prompt
        - Call Groq in structured JSON format
        - Parse outcomes and enforce safety disclosures
        """
        query = str(input_data).strip()
        patient_id = context.patient_id if context else None
        
        start_time = time.perf_counter()
        retrieval_start = time.perf_counter()
        
        # 1. Query Qdrant retrieval contexts
        retrieval_res = await self.retrieval_agent.run(query, context)
        retrieval_latency = (time.perf_counter() - retrieval_start) * 1000.0
        
        retrieval_data = retrieval_res.response or {}
        retrieved_context = retrieval_data.get("context", "")
        citations_raw = retrieval_data.get("retrieved_chunks", [])
        
        citations = []
        for c in citations_raw:
            citations.append({
                "source": c.get("metadata", {}).get("source", "medical_knowledge"),
                "text": c.get("text", "")[:200] + "...",
                "score": c.get("score", 0.0)
            })

        # 2. Query patient history details
        patient_context_str = "No patient context available."
        if patient_id:
            try:
                patient_context_res = await self.patient_context_service.assemble_context(patient_id)
                patient_context_str = self._format_patient_context(patient_context_res)
            except Exception as e:
                self.logger.warning(f"Failed to assemble patient context: {str(e)}")

        # 3. Formulate prompts
        try:
            rendered_system = render_core_prompt("symptom_analysis_system", {}, is_system=True)
            rendered_user = render_core_prompt("symptom_analysis_user", {
                "patient_context": patient_context_str,
                "retrieved_context": retrieved_context or "No symptom reference text retrieved.",
                "query": query
            })
        except Exception as e:
            self.logger.error(f"Failed to render symptom templates: {str(e)}")
            rendered_system = "You are a clinical symptom guidance agent. Return valid JSON containing summary, possible_causes, red_flags, recommended_action, and emergency keys."
            rendered_user = f"Context:\n{retrieved_context}\n\nSymptoms: {query}"

        # 4. Invoke LLM structured JSON output
        groq_start = time.perf_counter()
        ai_res = await self.ai_service.generate(
            prompt=rendered_user,
            system_prompt=rendered_system,
            request_id=context.request_id if context else None
        )
        groq_latency = (time.perf_counter() - groq_start) * 1000.0
        
        total_latency = (time.perf_counter() - start_time) * 1000.0

        # Parse structured output variables
        parsed_json = clean_json_response(ai_res.response) or {}
        
        summary = parsed_json.get("summary", "Symptom check completed.")
        possible_causes = parsed_json.get("possible_causes", [])
        red_flags = parsed_json.get("red_flags", [])
        recommended_action = parsed_json.get("recommended_action", "Consult a doctor if symptoms persist.")
        emergency = bool(parsed_json.get("emergency", False))

        # Enforce regulatory notices if missing
        notice = "This symptom summary is for informational purposes only and is not a substitute for professional medical advice, diagnosis, or treatment."
        if notice.lower() not in summary.lower():
            summary = f"{summary}\n\nDisclaimer: {notice}"

        # Enforce emergency escalation notice if emergency flag is true
        if emergency:
            emergency_warning = "CRITICAL WARNING: Life-threatening indicators detected. Please seek immediate medical care or visit the nearest emergency room."
            if emergency_warning.lower() not in recommended_action.lower():
                recommended_action = f"{emergency_warning}\n\n{recommended_action}"

        agent_res = SymptomAgentResponse(
            summary=summary,
            possible_causes=possible_causes,
            red_flags=red_flags,
            recommended_action=recommended_action,
            emergency=emergency,
            citations=citations,
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

        # 5. Record telemetry
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
