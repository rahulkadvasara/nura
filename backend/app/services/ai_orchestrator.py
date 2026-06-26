"""
Nura - AI Orchestration Service
Coordinates all AI components into a unified execution pipeline
"""
import time
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from app.core.ai_config import ai_settings
from app.utils.ai import orchestrator_metrics, estimate_cost
from app.services.groq_service import GroqService
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.services.patient_context_service import PatientContextService
from app.prompts.loader import PromptLoader
from app.schemas.ai import (
    AIPlaygroundChatRequest,
    AIPlaygroundChatResponse,
    AIExecutionSession
)

logger = logging.getLogger("nura.ai.orchestrator")


class AIOrchestrator:
    """Orchestrator managing prompt loadings, user queries validation, patient profiles context compilation, LLM calls, and metrics telemetry logging"""

    def __init__(
        self,
        groq_service: GroqService,
        embedding_service: EmbeddingService,
        vector_service: VectorService,
        patient_context_service: PatientContextService,
        prompt_loader: PromptLoader
    ):
        self.groq_service = groq_service
        self.embedding_service = embedding_service
        self.vector_service = vector_service
        self.patient_context_service = patient_context_service
        self.prompt_loader = prompt_loader

    async def execute_chat(
        self,
        request: AIPlaygroundChatRequest,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> AIPlaygroundChatResponse:
        """Standardized AI query execution pipeline run with patient context integration, cost, and latency metrics collection"""
        start_time = datetime.now(timezone.utc)
        start_perf = time.perf_counter()
        req_id = request_id or str(uuid.uuid4())
        
        # Determine model
        target_model = request.model or self.groq_service.settings.GROQ_MODEL
        
        # Telemetry metrics variables
        success = False
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        cost = 0.0
        response_text = ""
        error_msg = None
        context_sections = []
        patient_context_str = ""

        # 1. Validation
        if not request.prompt or not request.prompt.strip():
            error_msg = "User prompt cannot be empty"
            logger.error(error_msg)
            
            end_time = datetime.now(timezone.utc)
            duration = (time.perf_counter() - start_perf) * 1000.0
            
            orchestrator_metrics.record_orchestration(
                llm_latency_ms=0.0,
                embedding_latency_ms=0.0,
                context_latency_ms=0.0,
                total_latency_ms=duration,
                success=False,
                tokens=0,
                cost=0.0,
                model=target_model
            )
            
            session = AIExecutionSession(
                request_id=req_id,
                user_id=user_id,
                patient_id=request.patient_id,
                model=target_model,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                tokens=0,
                cost=0.0,
                status="failed",
                errors=error_msg
            )
            return AIPlaygroundChatResponse(
                response="",
                execution_session=session,
                prompt_template="",
                patient_context_sections=[]
            )

        context_start = time.perf_counter()
        
        # 2. Assembling Patient Context from MongoDB
        try:
            if request.patient_id:
                # Compile patient context deterministically
                patient_context_res = await self.patient_context_service.assemble_context(request.patient_id)
                context_sections = patient_context_res.metadata.sections_returned
                
                # Format a summary string representing sections returned
                summary_parts = []
                if patient_context_res.patient_profile:
                    summary_parts.append(f"Name: {patient_context_res.patient_profile.get('full_name')}")
                if patient_context_res.medical_summary:
                    summary_parts.append(f"Summary: {patient_context_res.medical_summary}")
                if patient_context_res.current_conditions:
                    summary_parts.append(f"Conditions: {', '.join(patient_context_res.current_conditions)}")
                if patient_context_res.current_medications:
                    summary_parts.append(f"Medications: {', '.join(patient_context_res.current_medications)}")
                if patient_context_res.medication_allergies:
                    summary_parts.append(f"Allergies: {', '.join(patient_context_res.medication_allergies)}")
                
                patient_context_str = "\n".join(summary_parts) if summary_parts else "No records available for this patient."
            else:
                patient_context_str = "No patient context provided."
        except Exception as e:
            logger.error(f"Failed to compile patient context: {str(e)}")
            patient_context_str = "Error compiling patient context."

        context_latency = (time.perf_counter() - context_start) * 1000.0

        # 3. Prompt Template Loading
        prompt_start = time.perf_counter()
        compiled_system_prompt = ""
        compiled_user_prompt = ""
        try:
            compiled_system_prompt = self.prompt_loader.render(
                name="medical_assistant",
                variables={"patient_context": patient_context_str},
                is_system=True
            )
            compiled_user_prompt = self.prompt_loader.render(
                name="chat_prompt",
                variables={
                    "user_query": request.prompt,
                    "patient_context": patient_context_str
                },
                is_system=False
            )
        except Exception as e:
            error_msg = f"Prompt template rendering failed: {str(e)}"
            logger.error(error_msg)
            
            end_time = datetime.now(timezone.utc)
            duration = (time.perf_counter() - start_perf) * 1000.0
            
            orchestrator_metrics.record_orchestration(
                llm_latency_ms=0.0,
                embedding_latency_ms=0.0,
                context_latency_ms=context_latency,
                total_latency_ms=duration,
                success=False,
                tokens=0,
                cost=0.0,
                model=target_model
            )
            
            session = AIExecutionSession(
                request_id=req_id,
                user_id=user_id,
                patient_id=request.patient_id,
                model=target_model,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                tokens=0,
                cost=0.0,
                status="failed",
                errors=error_msg
            )
            return AIPlaygroundChatResponse(
                response="",
                execution_session=session,
                prompt_template="",
                patient_context_sections=context_sections
            )

        # 4. LLM call via Groq
        llm_start = time.perf_counter()
        try:
            raw_response = await self.groq_service.generate(
                prompt=compiled_user_prompt,
                system_prompt=compiled_system_prompt,
                model=target_model,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            response_text = raw_response.choices[0].message.content or ""
            
            if raw_response.usage:
                prompt_tokens = raw_response.usage.prompt_tokens
                completion_tokens = raw_response.usage.completion_tokens
                total_tokens = raw_response.usage.total_tokens

            success = True
        except Exception as e:
            error_msg = f"LLM generation failed: {str(e)}"
            logger.error(error_msg)

        llm_latency = (time.perf_counter() - llm_start) * 1000.0
        
        # Calculate cost
        cost = estimate_cost(target_model, prompt_tokens, completion_tokens)
        
        end_time = datetime.now(timezone.utc)
        duration = (time.perf_counter() - start_perf) * 1000.0
        
        # Record telemetry metrics
        orchestrator_metrics.record_orchestration(
            llm_latency_ms=llm_latency,
            embedding_latency_ms=0.0,
            context_latency_ms=context_latency,
            total_latency_ms=duration,
            success=success,
            tokens=total_tokens,
            cost=cost,
            model=target_model
        )

        session = AIExecutionSession(
            request_id=req_id,
            user_id=user_id,
            patient_id=request.patient_id,
            model=target_model,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            tokens=total_tokens,
            cost=cost,
            status="success" if success else "failed",
            errors=error_msg
        )

        # HIPAA security logger: trace metrics and templates used, but NEVER log user inputs or PHI text content
        logger.info(
            f"AI Orchestration completed request {req_id} status={session.status}",
            extra={
                "request_id": req_id,
                "user_id": user_id,
                "patient_id": request.patient_id,
                "model": target_model,
                "token_usage": total_tokens,
                "cost": cost,
                "llm_latency_ms": llm_latency,
                "context_latency_ms": context_latency,
                "duration_ms": duration,
                "system_prompt_template": "medical_assistant",
                "user_prompt_template": "chat_prompt",
                "status": session.status
            }
        )

        return AIPlaygroundChatResponse(
            response=response_text if success else "",
            execution_session=session,
            prompt_template=compiled_user_prompt if success else "",
            patient_context_sections=context_sections
        )

    async def health_check(self) -> Dict[str, Any]:
        """Perform system connectivity health checks across all AI infrastructure sub-services"""
        # Groq
        groq_health = await self.groq_service.health_check()
        
        # Embedding
        embedding_health = await self.embedding_service.health_check()
        
        # Vector Client status check
        try:
            vector_health = await self.vector_service.health()
        except Exception as e:
            vector_health = {"connected": False, "status": "unhealthy", "error": str(e)}

        # Prompt loader template checking
        prompt_status = "healthy"
        try:
            self.prompt_loader.get_template("chat_prompt")
        except Exception as e:
            prompt_status = f"unhealthy: {str(e)}"
            
        prompt_registry = {
            "status": "healthy" if prompt_status == "healthy" else "unhealthy",
            "error": None if prompt_status == "healthy" else prompt_status,
            "version": "1.0.0",
            "templates_count": len(self.prompt_loader.versions)
        }

        # Context builder checking
        context_status = "healthy"
        try:
            await self.patient_context_service.user_repository.exists({})
        except Exception as e:
            context_status = f"unhealthy: {str(e)}"

        context_builder = {
            "status": "healthy" if context_status == "healthy" else "unhealthy",
            "error": None if context_status == "healthy" else context_status
        }

        return {
            "groq": groq_health,
            "embedding": embedding_health,
            "vector": vector_health,
            "prompt_registry": prompt_registry,
            "context_builder": context_builder
        }
