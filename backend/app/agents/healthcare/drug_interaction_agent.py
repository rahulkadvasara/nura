"""
Nura - Drug Interaction Agent
Concrete deterministic Agent for validating medication safety and drug-drug interactions.
"""

import time
import logging
from typing import Any, Optional, Dict, List

from app.agents.base.base_agent import BaseAgent
from app.agents.base.context import AgentContext
from app.agents.healthcare.schemas import DrugInteractionAgentResponse
from app.agents.healthcare.telemetry import get_healthcare_agents_telemetry
from app.core.ai_config import ai_settings
from app.services.ai_service import AIService
from app.agents.retrieval_agent import RetrievalAgent
from app.repositories.patient_memory_repository import PatientMemoryRepository

logger = logging.getLogger("nura.agents.healthcare.drug_interaction_agent")


class DrugInteractionAgent(BaseAgent):
    """Deterministic agent analyzing drug-drug interactions and safety disclaimers using ValidationService."""

    def __init__(
        self,
        retrieval_agent: RetrievalAgent,
        patient_memory_repository: PatientMemoryRepository,
        ai_service: AIService,
        validation_service: Optional[Any] = None,
        settings=None
    ):
        super().__init__(name="DrugInteractionAgent", settings=settings or ai_settings)
        self.retrieval_agent = retrieval_agent
        self.patient_memory_repository = patient_memory_repository
        self.ai_service = ai_service
        self.validation_service = validation_service
        self.telemetry = get_healthcare_agents_telemetry()

    def _format_patient_memory(self, memory: Any) -> str:
        """Helper to format memory details for telemetry/logging if needed"""
        if not memory:
            return "No profile memory aggregated."
            
        lines = []
        lines.append(f"Chronic Conditions: {', '.join(memory.chronic_conditions or [])}")
        lines.append(f"Allergies: {', '.join(memory.allergies or [])}")
        lines.append(f"Active Medications: {', '.join(memory.medications or [])}")
        return "\n".join(lines)

    async def execute(self, input_data: Any, context: Optional[AgentContext] = None) -> Any:
        """
        Execute Drug Interaction safety diagnostic using deterministic MedicationValidationService:
        - Parses medication name from query input.
        - Resolves patient_id from agent context.
        - Runs validation service checks.
        - Formulates deterministic DrugInteractionAgentResponse.
        """
        query_str = str(input_data).strip()
        patient_id = context.patient_id if context else None
        
        start_time = time.perf_counter()
        
        if not patient_id:
            patient_id = "system_test" # Fallback for local sandbox runs without explicit context

        # 1. Parse incoming medication names from input query string
        # Clean prefix like "Check safety parameters for:"
        prefix = "Check safety parameters for:"
        if query_str.lower().startswith(prefix.lower()):
            query_str = query_str[len(prefix):].strip()
            
        incoming_meds = [med.strip() for med in query_str.split(",") if med.strip()]
        if not incoming_meds:
            incoming_meds = ["medication"]

        # Ensure validation service is available
        if not self.validation_service:
            from app.core.dependencies import get_medication_validation_service
            self.validation_service = get_medication_validation_service()

        # 2. Run MedicationValidationService check
        val_res = await self.validation_service.validate_medications(
            patient_id=patient_id,
            incoming_medications=incoming_meds,
            source="reminder" # Trace validation source
        )

        interaction_found = val_res["decision"] in ("WARNING", "BLOCK")
        severity = val_res["severity"]
        recommendations = val_res["recommendations"]
        detected_interactions = val_res["detected_interactions"]
        
        # Build warnings list
        warnings = [item.description for item in detected_interactions]

        # Build citations
        citations = []
        for inter in detected_interactions:
            citations.append({
                "source": "drug_interactions",
                "text": f"{inter.drug_a} and {inter.drug_b} interaction: {inter.description}",
                "score": 1.0
            })

        # Enforce clinical disclaimers in the interaction summary
        notice = "This drug safety check is for informational purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always consult your physician before starting, stopping, or changing any medication."
        interaction_summary = " ".join(recommendations)
        interaction_summary = f"{interaction_summary}\n\nDisclaimer: {notice}"

        # Standardize severity formatting for legacy agent schemas
        if severity == "NONE":
            severity = "LOW"
        elif severity == "UNKNOWN":
            severity = "LOW"

        total_latency = (time.perf_counter() - start_time) * 1000.0

        agent_res = DrugInteractionAgentResponse(
            interaction_found=interaction_found,
            severity=severity,
            interaction_summary=interaction_summary,
            warnings=warnings,
            alternatives=[],
            citations=citations,
            metadata={
                "retrieval_latency_ms": 0.0,
                "groq_latency_ms": 0.0,
                "total_latency_ms": total_latency,
                "prompt_version": "1.0.0-deterministic"
            },
            usage={
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        )

        # 3. Record telemetry on the legacy agent telemetry dashboard
        self.telemetry.record_run(
            agent_name=self.name,
            latency_ms=total_latency,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            estimated_cost=0.0,
            success=True,
            retrieval_latency_ms=0.0,
            groq_latency_ms=0.0,
            citation_count=0
        )
        
        return agent_res
