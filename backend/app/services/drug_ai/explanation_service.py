import time
import copy
import asyncio
from typing import List, Dict, Any, Optional, Tuple

from app.services.groq_service import GroqService
from app.services.drug_ai.prompt_builder import DrugPromptLoader, DrugPromptBuilder
from app.services.drug_ai.fallback_service import DrugExplanationFallbackService
from app.services.drug_ai.telemetry import get_drug_ai_telemetry
from app.core.logging import get_logger
from app.services.drug_cache.drug_cache_service import get_drug_cache_service
from app.services.drug_safety.telemetry import drug_safety_telemetry
from app.utils.circuit_breaker import get_circuit_breaker

logger = get_logger("nura.ai.drug_explanation")

class DrugExplanationService:
    """AI Service that builds rich patient and clinician narrative drug safety explanations using Groq"""

    def __init__(self, groq_service: GroqService):
        self.groq_service = groq_service
        self.loader = DrugPromptLoader()
        self.builder = DrugPromptBuilder(self.loader)
        self.telemetry = get_drug_ai_telemetry()
        self.cache_service = get_drug_cache_service()
        self.ai_explanation_breaker = get_circuit_breaker("ai_explanation_service", failure_threshold=5, recovery_timeout=30.0)

    async def explain_safety(
        self,
        medications: List[str],
        severity: str,
        recommendations: List[str],
        interactions: List[Dict[str, Any]],
        patient_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Runs parallel generation of patient and doctor explanations, precautions, and summaries"""
        start_time = time.perf_counter()
        
        # 1. Check cache first
        cached_val = self.cache_service.get_explanation(interactions, patient_id)
        if cached_val is not None:
            res = copy.deepcopy(cached_val)
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            res["latency_ms"] = round(latency_ms, 2)
            
            # Record telemetry
            self.telemetry.record_request()
            self.telemetry.record_success(
                model_used=res.get("model_used", "cached"),
                prompt_tokens=0,
                completion_tokens=0,
                latency_ms=latency_ms
            )
            drug_safety_telemetry.record_explanation(
                latency_ms=latency_ms,
                prompt_tokens=0,
                completion_tokens=0,
                cost=0.0,
                fallback_used=res.get("fallback_used", False)
            )
            return res

        # 2. Build prompts
        patient_prompt = self.builder.build_patient_explanation(medications, severity, recommendations, interactions)
        doctor_prompt = self.builder.build_doctor_explanation(medications, severity, recommendations, interactions)
        summary_prompt = self.builder.build_interaction_summary(medications, severity, recommendations, interactions)
        precautions_prompt = self.builder.build_medication_precautions(medications, severity, recommendations, interactions)

        system_prompt = self.loader.get_template("drug_system", is_system=True)

        fallback_used = False
        model_used = "groq-default"

        async def run_gen(prompt: str, fallback_func) -> Tuple[str, int, int, str]:
            nonlocal fallback_used, model_used
            try:
                res = await self.groq_service.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=0.2
                )
                
                content = getattr(getattr(res, "choices", [None])[0], "message", None)
                content_str = getattr(content, "content", "") if content else ""
                
                if not content_str or "Service temporarily unavailable" in content_str:
                    logger.warning("GroqService returned fallback response. Triggering local fallback.")
                    fallback_used = True
                    return fallback_func(), 0, 0, "fallback-local"

                usage = getattr(res, "usage", None)
                p_tok = getattr(usage, "prompt_tokens", 0) if usage else 0
                c_tok = getattr(usage, "completion_tokens", 0) if usage else 0
                m_name = getattr(res, "model", "groq")

                return content_str, p_tok, c_tok, m_name

            except Exception as e:
                logger.error(f"Groq explanation generation failed: {e}. Executing local fallback.")
                fallback_used = True
                return fallback_func(), 0, 0, "fallback-local"

        async def generate_narratives():
            # Parallel executions
            tasks = [
                run_gen(patient_prompt, lambda: DrugExplanationFallbackService.generate_patient_explanation(severity, recommendations)),
                run_gen(doctor_prompt, lambda: DrugExplanationFallbackService.generate_doctor_explanation(severity, recommendations, interactions)),
                run_gen(summary_prompt, lambda: DrugExplanationFallbackService.generate_summary(severity, medications, interactions)),
                run_gen(precautions_prompt, lambda: DrugExplanationFallbackService.generate_precautions(severity))
            ]
            return await asyncio.gather(*tasks)

        # 3. Execute narrative generation wrapped in Circuit Breaker
        try:
            results = await self.ai_explanation_breaker.execute_async(generate_narratives)
        except Exception as e:
            logger.error(f"Circuit breaker AI generation call failed: {e}. Triggering offline local fallback.")
            fallback_used = True
            results = [
                (DrugExplanationFallbackService.generate_patient_explanation(severity, recommendations), 0, 0, "fallback-local"),
                (DrugExplanationFallbackService.generate_doctor_explanation(severity, recommendations, interactions), 0, 0, "fallback-local"),
                (DrugExplanationFallbackService.generate_summary(severity, medications, interactions), 0, 0, "fallback-local"),
                (DrugExplanationFallbackService.generate_precautions(severity), 0, 0, "fallback-local")
            ]

        patient_explanation, p_p_tok, p_c_tok, p_m = results[0]
        doctor_explanation, d_p_tok, d_c_tok, d_m = results[1]
        summary, s_p_tok, s_c_tok, s_m = results[2]
        precautions, pr_p_tok, pr_c_tok, pr_m = results[3]

        prompt_tokens = p_p_tok + d_p_tok + s_p_tok + pr_p_tok
        completion_tokens = p_c_tok + d_c_tok + s_c_tok + pr_c_tok
        
        # Determine model used
        for m in (p_m, d_m, s_m, pr_m):
            if m and m != "fallback-local":
                model_used = m
                break

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        # Record prompt/completion costs
        cost = (prompt_tokens * 0.00000015) + (completion_tokens * 0.00000060)

        # Record telemetry
        self.telemetry.record_request()
        if fallback_used:
            self.telemetry.record_fallback()
        else:
            self.telemetry.record_success(model_used, prompt_tokens, completion_tokens, latency_ms)

        drug_safety_telemetry.record_explanation(
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost=cost,
            fallback_used=fallback_used
        )

        response = {
            "patient_explanation": patient_explanation,
            "doctor_explanation": doctor_explanation,
            "precautions": precautions,
            "summary": summary,
            "fallback_used": fallback_used,
            "latency_ms": round(latency_ms, 2),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "estimated_cost": round(cost, 6),
            "model_used": model_used
        }

        # 4. Update Cache
        self.cache_service.set_explanation(interactions, response, patient_id)

        return response


_explanation_service_instance: Optional[DrugExplanationService] = None

def get_drug_explanation_service(groq_service: Optional[GroqService] = None) -> DrugExplanationService:
    global _explanation_service_instance
    if _explanation_service_instance is None:
        from app.services.groq_service import get_groq_service
        service = groq_service or get_groq_service()
        _explanation_service_instance = DrugExplanationService(groq_service=service)
    return _explanation_service_instance
