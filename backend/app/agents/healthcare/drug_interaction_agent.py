"""
Nura - Drug Interaction Agent
Concrete AI Agent for validating medication safety, allergy conflicts, and drug-drug interactions.
"""

import time
from typing import Any, Optional, Dict, List

from app.agents.base.base_agent import BaseAgent
from app.agents.base.context import AgentContext
from app.agents.healthcare.schemas import DrugInteractionAgentResponse
from app.agents.healthcare.prompts import render_healthcare_prompt
from app.agents.healthcare.telemetry import get_healthcare_agents_telemetry
from app.agents.healthcare.utils import clean_json_response
from app.core.ai_config import ai_settings
from app.services.ai_service import AIService
from app.agents.retrieval_agent import RetrievalAgent
from app.repositories.patient_memory_repository import PatientMemoryRepository


class DrugInteractionAgent(BaseAgent):
    """Production agent analyzing drug-drug interactions, allergy conflicts, and safety disclaimers"""

    def __init__(
        self,
        retrieval_agent: RetrievalAgent,
        patient_memory_repository: PatientMemoryRepository,
        ai_service: AIService,
        settings=None
    ):
        super().__init__(name="DrugInteractionAgent", settings=settings or ai_settings)
        self.retrieval_agent = retrieval_agent
        self.patient_memory_repository = patient_memory_repository
        self.ai_service = ai_service
        self.telemetry = get_healthcare_agents_telemetry()

    def _format_patient_memory(self, memory: Any) -> str:
        """Helper to format memory details for prompt usage"""
        if not memory:
            return "No profile memory aggregated."
            
        lines = []
        lines.append(f"AI longitudinal Summary: {memory.ai_summary or 'None'}")
        lines.append(f"Chronic Conditions: {', '.join(memory.chronic_conditions or [])}")
        lines.append(f"Allergies: {', '.join(memory.allergies or [])}")
        lines.append(f"Active Medications: {', '.join(memory.medications or [])}")
        lines.append(f"Diagnoses: {', '.join(memory.diagnoses or [])}")
        return "\n".join(lines)

    async def execute(self, input_data: Any, context: Optional[AgentContext] = None) -> Any:
        """
        Execute Drug Interaction safety diagnostic:
        - Query Qdrant via RetrievalAgent
        - Load patient memory from MongoDB PatientMemoryRepository
        - Render prompt
        - Call Groq in structured JSON format
        - Parse outcomes and enforce safety disclosures
        """
        query = str(input_data).strip()
        patient_id = context.patient_id if context else None
        
        start_time = time.perf_counter()
        retrieval_start = time.perf_counter()
        
        # 1. Query Qdrant drug safety guidelines (Force intent to drug_question)
        retrieval_ctx = context.model_copy(update={
            "metadata": {
                **(context.metadata or {}),
                "intent": "drug_question"
            }
        }) if context else AgentContext(metadata={"intent": "drug_question"})

        retrieval_res = await self.retrieval_agent.run(query, retrieval_ctx)
        retrieval_latency = (time.perf_counter() - retrieval_start) * 1000.0
        
        retrieval_data = retrieval_res.response or {}
        retrieved_context = retrieval_data.get("context", "")
        citations_raw = retrieval_data.get("retrieved_chunks", [])
        
        citations = []
        for c in citations_raw:
            citations.append({
                "source": c.get("metadata", {}).get("source", "drug_knowledge"),
                "text": c.get("text", "")[:200] + "...",
                "score": c.get("score", 0.0)
            })

        # 2. Query patient memory details
        patient_memory_str = "No patient memory details available."
        if patient_id:
            try:
                patient_mem = await self.patient_memory_repository.get_by_patient_id(patient_id)
                patient_memory_str = self._format_patient_memory(patient_mem)
            except Exception as e:
                self.logger.warning(f"Failed to load patient memory: {str(e)}")

        # 3. Formulate prompts
        try:
            rendered_system = render_healthcare_prompt("drug_interaction_system", {}, is_system=True)
            rendered_user = render_healthcare_prompt("drug_interaction_user", {
                "patient_context": patient_memory_str,
                "retrieved_context": retrieved_context or "No drug interaction guidelines retrieved.",
                "query": query
            })
        except Exception as e:
            self.logger.error(f"Failed to render drug templates: {str(e)}")
            rendered_system = "You are a clinical medication safety agent. Return valid JSON containing interaction_found, severity, interaction_summary, warnings, and alternatives."
            rendered_user = f"Context:\n{retrieved_context}\n\nPatient Memory:\n{patient_memory_str}\n\nQuery: {query}"

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
        
        interaction_found = bool(parsed_json.get("interaction_found", False))
        severity = parsed_json.get("severity", "LOW").upper()
        interaction_summary = parsed_json.get("interaction_summary", "Medication validation completed.")
        warnings = parsed_json.get("warnings", [])
        alternatives = parsed_json.get("alternatives", [])

        # Enforce clinical disclaimers
        notice = "This drug safety check is for informational purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always consult your physician before starting, stopping, or changing any medication."
        if notice.lower() not in interaction_summary.lower():
            interaction_summary = f"{interaction_summary}\n\nDisclaimer: {notice}"

        if severity not in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
            severity = "LOW"

        agent_res = DrugInteractionAgentResponse(
            interaction_found=interaction_found,
            severity=severity,
            interaction_summary=interaction_summary,
            warnings=warnings,
            alternatives=alternatives,
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
            groq_latency_ms=groq_latency,
            citation_count=len(citations)
        )
        
        return agent_res
