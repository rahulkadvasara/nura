"""
Nura - Doctor Recommendation Agent
Concrete AI Agent for recommending suitable doctors based on symptoms, specialty, and availability.
"""

import time
from typing import Any, Optional, Dict, List

from app.agents.base.base_agent import BaseAgent
from app.agents.base.context import AgentContext
from app.agents.healthcare.schemas import DoctorRecommendationAgentResponse
from app.agents.healthcare.prompts import render_healthcare_prompt
from app.agents.healthcare.telemetry import get_healthcare_agents_telemetry
from app.agents.healthcare.utils import clean_json_response
from app.core.ai_config import ai_settings
from app.services.ai_service import AIService
from app.services.patient_context_service import PatientContextService
from app.agents.retrieval_agent import RetrievalAgent
from app.repositories.doctor_repository import DoctorAvailabilityRepository


class DoctorRecommendationAgent(BaseAgent):
    """Production agent recommending doctors using specialty matching and availability lookups"""

    def __init__(
        self,
        retrieval_agent: RetrievalAgent,
        patient_context_service: PatientContextService,
        doctor_availability_repository: DoctorAvailabilityRepository,
        ai_service: AIService,
        settings=None
    ):
        super().__init__(name="DoctorRecommendationAgent", settings=settings or ai_settings)
        self.retrieval_agent = retrieval_agent
        self.patient_context_service = patient_context_service
        self.doctor_availability_repository = doctor_availability_repository
        self.ai_service = ai_service
        self.telemetry = get_healthcare_agents_telemetry()

    def _format_patient_context(self, context_res: Any) -> str:
        """Utility to serialize structured PatientContextResponse into prompt string"""
        if not context_res:
            return "No patient context available."
            
        parts = []
        if getattr(context_res, "patient_profile", None):
            p = context_res.patient_profile
            parts.append(f"Patient Name: {p.get('full_name', 'Patient')}")
            location = p.get("location") or p.get("city") or p.get("address")
            if location:
                parts.append(f"Patient Location: {location}")
        if getattr(context_res, "medical_summary", None):
            parts.append(f"Medical Summary: {context_res.medical_summary}")
        if getattr(context_res, "current_conditions", None):
            parts.append(f"Chronic Conditions: {', '.join(context_res.current_conditions)}")
        return "\n".join(parts) if parts else "No patient context available."

    async def execute(self, input_data: Any, context: Optional[AgentContext] = None) -> Any:
        """
        Execute Doctor Recommendation pipeline:
        - Query Qdrant via RetrievalAgent
        - Query MongoDB for availability of matched doctors
        - Compile patient history from MongoDB
        - Render prompt
        - Call Groq in structured JSON format
        - Parse outcomes and enforce safety disclosures
        """
        query = str(input_data).strip()
        patient_id = context.patient_id if context else None
        
        start_time = time.perf_counter()
        retrieval_start = time.perf_counter()
        
        # 1. Query Qdrant doctor profiles (Force intent to doctor_recommendation)
        retrieval_ctx = context.model_copy(update={
            "metadata": {
                **(context.metadata or {}),
                "intent": "doctor_recommendation"
            }
        }) if context else AgentContext(metadata={"intent": "doctor_recommendation"})

        retrieval_res = await self.retrieval_agent.run(query, retrieval_ctx)
        retrieval_latency = (time.perf_counter() - retrieval_start) * 1000.0
        
        retrieval_data = retrieval_res.response or {}
        citations_raw = retrieval_data.get("retrieved_chunks", [])

        # 2. Query MongoDB for active availability slots of each retrieved doctor
        assembled_docs_list = []
        for match in citations_raw:
            payload = match.get("payload", {})
            doc_id = payload.get("doctor_id") or payload.get("id") or match.get("id")
            
            # Fetch slots from DB
            availability_str = "No availability slots declared"
            if doc_id:
                try:
                    slots = await self.doctor_availability_repository.get_active_by_doctor_id(str(doc_id))
                    if slots:
                        slots_details = []
                        for s in slots:
                            day = getattr(s, "day_of_week", "Unknown")
                            start = getattr(s, "start_time", "")
                            end = getattr(s, "end_time", "")
                            slots_details.append(f"{day}: {start}-{end}")
                        availability_str = ", ".join(slots_details)
                except Exception as e:
                    self.logger.warning(f"Failed to lookup doctor availability for {doc_id}: {str(e)}")

            assembled_docs_list.append(
                f"Doctor ID: {doc_id}\n"
                f"Name: {payload.get('full_name', 'Unknown')}\n"
                f"Specialization: {payload.get('specialization', 'General Medicine')}\n"
                f"Experience: {payload.get('experience_years', 'Unknown')} years\n"
                f"Languages: {', '.join(payload.get('languages', ['English']))}\n"
                f"Hospital: {payload.get('hospital', 'Nura Clinic')}\n"
                f"Availability: {availability_str}\n"
                f"Rating: {payload.get('average_rating', 'No rating')}\n"
                f"---"
            )

        retrieved_context = "\n".join(assembled_docs_list)

        # 3. Query patient history details
        patient_context_str = "No patient context available."
        if patient_id:
            try:
                patient_context_res = await self.patient_context_service.assemble_context(patient_id)
                patient_context_str = self._format_patient_context(patient_context_res)
            except Exception as e:
                self.logger.warning(f"Failed to assemble patient context: {str(e)}")

        # 4. Formulate prompts
        try:
            rendered_system = render_healthcare_prompt("doctor_recommendation_system", {}, is_system=True)
            rendered_user = render_healthcare_prompt("doctor_recommendation_user", {
                "patient_context": patient_context_str,
                "retrieved_context": retrieved_context or "No matching doctor profiles retrieved.",
                "query": query
            })
        except Exception as e:
            self.logger.error(f"Failed to render doctor templates: {str(e)}")
            rendered_system = "You are a doctor recommendation agent. Return valid JSON containing recommended_doctors, reasoning, matching_specialization, and confidence."
            rendered_user = f"Doctors Profiles:\n{retrieved_context}\n\nPatient Details:\n{patient_context_str}\n\nQuery: {query}"

        # 5. Invoke LLM structured JSON output
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
        
        recommended_doctors = parsed_json.get("recommended_doctors", [])
        reasoning = parsed_json.get("reasoning", "Doctor recommendation completed.")
        matching_specialization = parsed_json.get("matching_specialization", "General Medicine")
        confidence = float(parsed_json.get("confidence", 0.85))

        agent_res = DoctorRecommendationAgentResponse(
            recommended_doctors=recommended_doctors,
            reasoning=reasoning,
            matching_specialization=matching_specialization,
            confidence=confidence,
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

        # 6. Record telemetry
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
            citation_count=len(assembled_docs_list)
        )
        
        return agent_res
