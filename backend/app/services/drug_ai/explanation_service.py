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
        patient_id: Optional[str] = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Runs parallel generation of patient and doctor explanations, precautions, and summaries"""
        start_time = time.perf_counter()
        
        # 1. Check cache first (unless force_refresh is True)
        if not force_refresh:
            cached_val = self.cache_service.get_explanation(interactions, patient_id)
            if cached_val is not None:
                res = copy.deepcopy(cached_val)
                latency_ms = (time.perf_counter() - start_time) * 1000.0
                res["latency_ms"] = round(latency_ms, 2)
                return res
            
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

        # Fast path: If no interactions were detected, return concise safe response without firing LLM queries
        if not interactions or severity == "NONE":
            safe_text = "No safety risks detected for active medications."
            if medications:
                safe_text = f"Safety check complete. No known drug interactions or safety risks detected for: {', '.join(medications)}."
            res = {
                "patient_explanation": safe_text,
                "doctor_explanation": f"Clinical Evaluation: No active drug interactions or duplicate ingredient hazards detected for {', '.join(medications)}.",
                "summary": f"No safety risks detected for {', '.join(medications)}.",
                "precautions": "Continue medications as prescribed. Maintain regular hydration and consult a clinician if new symptoms develop.",
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "model_used": "fast-path",
                "estimated_cost": 0.0,
                "fallback_used": False,
                "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 2)
            }
            if not force_refresh:
                self.cache_service.set_explanation(interactions, res, patient_id)
            return res

        # 2. Build patient explanation prompt (Single efficient LLM call)
        patient_prompt = self.builder.build_patient_explanation(medications, severity, recommendations, interactions)
        system_prompt = self.loader.get_template("drug_system", is_system=True)

        fallback_used = False
        model_used = "groq-default"

        async def generate_patient_narrative() -> Tuple[str, int, int, str]:
            nonlocal fallback_used, model_used
            try:
                res = await self.groq_service.generate(
                    prompt=patient_prompt,
                    system_prompt=system_prompt,
                    temperature=0.2
                )
                
                content = getattr(getattr(res, "choices", [None])[0], "message", None)
                content_str = getattr(content, "content", "") if content else ""
                
                if not content_str or "Service temporarily unavailable" in content_str:
                    logger.warning("GroqService returned fallback response. Triggering local fallback.")
                    fallback_used = True
                    return DrugExplanationFallbackService.generate_patient_explanation(severity, recommendations), 0, 0, "fallback-local"

                usage = getattr(res, "usage", None)
                p_tok = getattr(usage, "prompt_tokens", 0) if usage else 0
                c_tok = getattr(usage, "completion_tokens", 0) if usage else 0
                m_name = getattr(res, "model", "groq")

                return content_str, p_tok, c_tok, m_name

            except Exception as e:
                logger.error(f"Groq explanation generation failed: {e}. Executing local fallback.")
                fallback_used = True
                return DrugExplanationFallbackService.generate_patient_explanation(severity, recommendations), 0, 0, "fallback-local"

        # 3. Execute single LLM call wrapped in Circuit Breaker
        try:
            patient_explanation, prompt_tokens, completion_tokens, model_used = await self.ai_explanation_breaker.execute_async(generate_patient_narrative)
        except Exception as e:
            logger.error(f"Circuit breaker AI generation call failed: {e}. Triggering offline local fallback.")
            fallback_used = True
            patient_explanation = DrugExplanationFallbackService.generate_patient_explanation(severity, recommendations)
            prompt_tokens = 0
            completion_tokens = 0
            model_used = "fallback-local"

        doctor_explanation = DrugExplanationFallbackService.generate_doctor_explanation(severity, recommendations, interactions)
        summary = DrugExplanationFallbackService.generate_summary(severity, medications, interactions)
        precautions = DrugExplanationFallbackService.generate_precautions(severity)
        
        # Calculate latency and cost

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
