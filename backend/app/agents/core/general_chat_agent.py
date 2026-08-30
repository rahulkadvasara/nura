"""
Nura - General Chat Agent
Concrete AI Agent for answering assistant identity, capabilities, and conversational questions.
"""

import time
import logging
from typing import Any, Optional

from app.agents.base.base_agent import BaseAgent
from app.agents.base.context import AgentContext
from app.agents.core.schemas import GeneralChatAgentResponse
from app.agents.core.telemetry import get_core_agents_telemetry
from app.core.ai_config import ai_settings
from app.services.ai_service import AIService


class GeneralChatAgent(BaseAgent):
    """Production agent answering generic queries about Nura, capabilities, and general conversation"""

    def __init__(
        self,
        ai_service: Optional[AIService] = None,
        settings=None
    ):
        super().__init__(name="GeneralChatAgent", settings=settings or ai_settings)
        if ai_service is None:
            from app.core.dependencies import get_ai_service
            self.ai_service = get_ai_service()
        else:
            self.ai_service = ai_service

        self.telemetry = get_core_agents_telemetry()

    async def execute(self, input_data: Any, context: Optional[AgentContext] = None) -> GeneralChatAgentResponse:
        """
        Execute General Chat Pipeline:
        - Formulate informative, helpful assistant background and capability response
        """
        query = str(input_data).strip()
        start_time = time.perf_counter()

        system_prompt = (
            "You are Nura, an advanced AI healthcare assistant created to empower patients. "
            "You help users analyze lab reports, triage symptoms, evaluate medication interactions, "
            "recommend medical specialists, schedule appointments, and set medication reminders. "
            "Answer general conversation questions politely, concisely, and clearly. "
            "Always maintain a supportive and professional clinical tone."
        )

        try:
            groq_start = time.perf_counter()
            ai_res = await self.ai_service.generate(
                prompt=query,
                system_prompt=system_prompt,
                request_id=context.request_id if context else None
            )
            groq_latency = (time.perf_counter() - groq_start) * 1000.0
            response_text = ai_res.response
            prompt_tokens = ai_res.prompt_tokens
            completion_tokens = ai_res.completion_tokens
            total_tokens = ai_res.total_tokens
            cost = ai_res.estimated_cost
        except Exception as e:
            self.logger.error(f"GeneralChatAgent LLM generation failed: {e}", exc_info=True)
            response_text = (
                "I am Nura, your AI healthcare assistant. I can help you analyze medical lab reports, "
                "check symptoms, review medication safety, find doctor specialists, and manage your appointments."
            )
            groq_latency = 0.0
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0
            cost = 0.0

        total_latency = (time.perf_counter() - start_time) * 1000.0

        agent_res = GeneralChatAgentResponse(
            answer=response_text,
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
