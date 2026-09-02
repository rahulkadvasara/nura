"""
Nura - Greeting Agent
Concrete AI Agent for handling polite conversational greetings.
"""

import time
import logging
from typing import Any, Optional

from app.agents.base.base_agent import BaseAgent
from app.agents.base.context import AgentContext
from app.agents.core.schemas import GreetingAgentResponse
from app.agents.core.telemetry import get_core_agents_telemetry
from app.core.ai_config import ai_settings
from app.services.ai_service import AIService
from app.services.patient_context_service import PatientContextService


class GreetingAgent(BaseAgent):
    """Production agent managing greetings and welcoming user interactions"""

    def __init__(
        self,
        patient_context_service: Optional[PatientContextService] = None,
        ai_service: Optional[AIService] = None,
        settings=None
    ):
        super().__init__(name="GreetingAgent", settings=settings or ai_settings)
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

    async def execute(self, input_data: Any, context: Optional[AgentContext] = None) -> GreetingAgentResponse:
        """
        Execute Greeting Pipeline:
        - Fetch patient name if patient_id is present
        - Formulate friendly, empathetic greeting response
        """
        query = str(input_data).strip()
        patient_id = context.patient_id if context else None
        
        start_time = time.perf_counter()
        
        patient_name = "there"
        if patient_id:
            try:
                patient_context_res = await self.patient_context_service.assemble_context(patient_id)
                if patient_context_res and patient_context_res.patient_profile:
                    full_name = patient_context_res.patient_profile.get("full_name", "")
                    if full_name:
                        patient_name = full_name.split()[0]
            except Exception as e:
                self.logger.warning(f"GreetingAgent failed to fetch patient profile: {e}")

        if patient_name and patient_name.lower() != "there":
            response_text = f"Hello {patient_name}! I am Nura, your AI healthcare assistant. How can I assist you with your health, medical reports, symptoms, or appointments today?"
        else:
            response_text = "Hello! I am Nura, your AI healthcare assistant. How can I assist you with your health, medical reports, symptoms, or appointments today?"

        groq_latency = 0.0
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        cost = 0.0

        total_latency = (time.perf_counter() - start_time) * 1000.0

        agent_res = GreetingAgentResponse(
            greeting=response_text,
            metadata={
                "groq_latency_ms": groq_latency,
                "total_latency_ms": total_latency,
                "prompt_version": "1.0.0"
            },
            usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            }
        )

        self.telemetry.record_run(
            agent_name=self.name,
            latency_ms=total_latency,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost=cost,
            success=True,
            groq_latency_ms=groq_latency
        )

        return agent_res
