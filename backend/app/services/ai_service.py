"""
Nura - AI Orchestration Service
Central entry point for all AI capabilities, providing monitoring, metrics and logging
"""

import time
import uuid
from datetime import datetime, timezone
from typing import Optional, Any, AsyncGenerator
from pydantic import BaseModel

from app.core.logging import get_logger
from app.services.groq_service import GroqService, get_groq_service
from app.utils.ai import ai_metrics, estimate_cost

logger = get_logger("nura.ai.service")


class AIServiceResponse(BaseModel):
    """Normalized response schema returned by the AI Service"""
    response: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float
    finish_reason: str
    estimated_cost: float


class AIService:
    """Orchestrator service that sits between the application modules and the LLM API clients"""

    def __init__(self, groq_service: GroqService):
        self.groq_service = groq_service

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        request_id: Optional[str] = None,
        **kwargs
    ) -> AIServiceResponse:
        """Generate a response using Groq client, tracking execution telemetry"""
        req_id = request_id or str(uuid.uuid4())
        target_model = model or self.groq_service.settings.GROQ_MODEL
        start_time = time.perf_counter()
        status = "success"
        
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        finish_reason = "stop"
        response_text = ""

        try:
            raw_response = await self.groq_service.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                model=target_model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            # Normalize response payload and usage data
            response_text = raw_response.choices[0].message.content or ""
            finish_reason = raw_response.choices[0].finish_reason or "stop"
            
            if raw_response.usage:
                prompt_tokens = raw_response.usage.prompt_tokens
                completion_tokens = raw_response.usage.completion_tokens
                total_tokens = raw_response.usage.total_tokens

            latency_ms = (time.perf_counter() - start_time) * 1000.0
            
            # Record in-memory metrics
            ai_metrics.record_success(latency_ms, total_tokens)
            
            cost = estimate_cost(target_model, prompt_tokens, completion_tokens)
            
            return AIServiceResponse(
                response=response_text,
                model=target_model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                latency_ms=latency_ms,
                finish_reason=finish_reason,
                estimated_cost=cost
            )
            
        except Exception as e:
            status = "failed"
            ai_metrics.record_failure()
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            raise e
        finally:
            # Structured logging (without leaking prompt/response contents)
            logger.info(
                f"AI Request: request_id={req_id} model={target_model} latency={latency_ms:.2f}ms "
                f"prompt_tokens={prompt_tokens} completion_tokens={completion_tokens} status={status}",
                extra={
                    "request_id": req_id,
                    "model": target_model,
                    "latency": latency_ms,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "status": status,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )

    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        request_id: Optional[str] = None,
        **kwargs
    ) -> AIServiceResponse:
        """Generate a structured JSON response using Groq client, tracking execution telemetry"""
        req_id = request_id or str(uuid.uuid4())
        target_model = model or self.groq_service.settings.GROQ_MODEL
        start_time = time.perf_counter()
        status = "success"
        
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        finish_reason = "stop"
        response_text = ""

        try:
            raw_response = await self.groq_service.generate_json(
                prompt=prompt,
                system_prompt=system_prompt,
                model=target_model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            # Normalize response payload and usage data
            response_text = raw_response.choices[0].message.content or ""
            finish_reason = raw_response.choices[0].finish_reason or "stop"
            
            if raw_response.usage:
                prompt_tokens = raw_response.usage.prompt_tokens
                completion_tokens = raw_response.usage.completion_tokens
                total_tokens = raw_response.usage.total_tokens

            latency_ms = (time.perf_counter() - start_time) * 1000.0
            
            # Record in-memory metrics
            ai_metrics.record_success(latency_ms, total_tokens)
            
            cost = estimate_cost(target_model, prompt_tokens, completion_tokens)
            
            return AIServiceResponse(
                response=response_text,
                model=target_model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                latency_ms=latency_ms,
                finish_reason=finish_reason,
                estimated_cost=cost
            )
            
        except Exception as e:
            status = "failed"
            ai_metrics.record_failure()
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            raise e
        finally:
            # Structured logging (without leaking prompt/response contents)
            logger.info(
                f"AI JSON Request: request_id={req_id} model={target_model} latency={latency_ms:.2f}ms "
                f"prompt_tokens={prompt_tokens} completion_tokens={completion_tokens} status={status}",
                extra={
                    "request_id": req_id,
                    "model": target_model,
                    "latency": latency_ms,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "status": status,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )

    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        request_id: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[Any, None]:
        """Stream completion chunks directly from Groq service"""
        req_id = request_id or str(uuid.uuid4())
        target_model = model or self.groq_service.settings.GROQ_MODEL
        start_time = time.perf_counter()
        status = "success"

        try:
            async for chunk in self.groq_service.stream(
                prompt=prompt,
                system_prompt=system_prompt,
                model=target_model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            ):
                yield chunk
        except Exception as e:
            status = "failed"
            raise e
        finally:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            logger.info(
                f"AI Stream Request: request_id={req_id} model={target_model} latency={latency_ms:.2f}ms status={status}",
                extra={
                    "request_id": req_id,
                    "model": target_model,
                    "latency": latency_ms,
                    "status": status,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )


# Singleton reference cache
_ai_service_instance: Optional[AIService] = None

def get_ai_service(groq_service: Optional[GroqService] = None) -> AIService:
    """Retrieve singleton instance of AIService"""
    global _ai_service_instance
    if _ai_service_instance is None:
        g_service = groq_service or get_groq_service()
        _ai_service_instance = AIService(groq_service=g_service)
    return _ai_service_instance
