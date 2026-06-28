"""
Nura - Clinical Report AI Summarization & Understanding Service
"""

import json
import time
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from app.models.report import ReportInDB
from app.repositories.report_repository import ReportRepository
from app.services.ai_service import AIService
from app.agents.healthcare.report_analysis_agent import ReportAnalysisAgent
from app.agents.base.context import AgentContext
from app.services.report_ai.utils import ReportPromptLoader
from app.services.report_ai.summary_service import SummaryService
from app.services.report_ai.insight_service import InsightService
from app.services.report_ai.telemetry import get_report_ai_telemetry

logger = logging.getLogger("nura.report_ai.report_understanding_service")


class ReportUnderstandingService:
    """Master orchestrator for generating executive clinical summaries, patient-friendly explanations, and doctor insights"""

    def __init__(
        self,
        report_repository: ReportRepository,
        ai_service: AIService,
        report_analysis_agent: ReportAnalysisAgent,
        prompt_loader: ReportPromptLoader,
        summary_service: SummaryService,
        insight_service: InsightService
    ):
        self.report_repository = report_repository
        self.ai_service = ai_service
        self.report_analysis_agent = report_analysis_agent
        self.prompt_loader = prompt_loader
        self.summary_service = summary_service
        self.insight_service = insight_service

    async def generate_report_summary(self, report_id: str) -> Optional[ReportInDB]:
        """Runs the clinical AI summarization run loop and saves structured outcomes to MongoDB"""
        start_time = time.time()
        
        # 1. Fetch report details from DB
        report = await self.report_repository.get(report_id)
        if not report:
            logger.error(f"Report {report_id} not found for AI summarization")
            return None

        patient_id = report.patient_id
        struct_data = getattr(report, "structured_data", {}) or {}
        patient_info = struct_data.get("patient_information") or {}
        labs = getattr(report, "laboratory_results", []) or []
        medications = getattr(report, "medications", []) or []
        risk_findings = getattr(report, "risk_findings", []) or []
        recommendations = getattr(report, "recommendations", []) or []

        # 2. Run ReportAnalysisAgent for history context
        history_context = "No previous medical reports history available."
        try:
            agent_ctx = AgentContext(patient_id=patient_id)
            agent_query = f"Provide a historical trend review and summary of report findings for patient {patient_id}."
            agent_res = await self.report_analysis_agent.run(agent_query, agent_ctx)
            if agent_res and agent_res.success:
                resp_data = agent_res.response
                summary_text = getattr(resp_data, "summary", "") or ""
                trends = getattr(resp_data, "trend_analysis", []) or []
                history_context = (
                    f"AI History Summary: {summary_text}\n"
                    f"Identified Trends: {', '.join(trends) if trends else 'None'}"
                )
        except Exception as err:
            logger.warning(f"Failed to query ReportAnalysisAgent for historical context: {err}")

        # 3. Format inputs for rendering prompt templates
        demographics_str = json.dumps(patient_info)
        
        labs_list = []
        for l in labs:
            labs_list.append(
                f"- Parameter: {l.get('test_name')} | Value: {l.get('value')} {l.get('unit', '')} | "
                f"Range: {l.get('reference_range')} | Status: {l.get('status')}"
            )
        labs_str = "\n".join(labs_list) if labs_list else "No laboratory results parameters."

        findings_list = []
        for f in risk_findings:
            findings_list.append(
                f"- Finding: {f.get('finding_name')} | Severity: {f.get('severity')} | Message: {f.get('message')}"
            )
        findings_str = "\n".join(findings_list) if findings_list else "No clinical risks flagged."

        recs_list = []
        for r in recommendations:
            recs_list.append(
                f"- Recommendation: {r.get('recommendation_type')} | Urgency: {r.get('urgency')} | Description: {r.get('description')}"
            )
        recs_str = "\n".join(recs_list) if recs_list else "No recommendations."

        # 4. Formulate prompts
        try:
            system_prompt = self.prompt_loader.render("report_summary_system", {}, is_system=True)
            
            p_prompt = self.prompt_loader.render("patient_summary", {
                "demographics": demographics_str,
                "lab_results": labs_str,
                "risk_findings": findings_str,
                "history_context": history_context
            })
            
            d_prompt = self.prompt_loader.render("doctor_summary", {
                "demographics": demographics_str,
                "lab_results": labs_str,
                "risk_findings": findings_str,
                "history_context": history_context
            })
            
            i_prompt = self.prompt_loader.render("clinical_insights", {
                "demographics": demographics_str,
                "lab_results": labs_str,
                "risk_findings": findings_str,
                "history_context": history_context
            })
            
            q_prompt = self.prompt_loader.render("followup_questions", {
                "risk_findings": findings_str,
                "recommendations": recs_str
            })

            user_prompt = (
                f"=== Patient friendly summary instructions ===\n{p_prompt}\n\n"
                f"=== Doctor summary instructions ===\n{d_prompt}\n\n"
                f"=== Key findings and clinical insights instructions ===\n{i_prompt}\n\n"
                f"=== Follow-up suggested questions instructions ===\n{q_prompt}\n"
            )
        except Exception as err:
            logger.error(f"Failed to render summarization prompt templates: {err}", exc_info=True)
            system_prompt = "You are a clinical summarizer. Respond with valid JSON."
            user_prompt = f"Labs: {labs_str}\nRisks: {findings_str}"

        # 5. Call LLM Groq JSON API
        success = False
        model_used = "groq-model"
        prompt_tokens = 0
        completion_tokens = 0
        cost = 0.0
        latency_ms = 0.0

        try:
            start_groq = time.perf_counter()
            ai_res = await self.ai_service.generate_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.1
            )
            latency_ms = (time.perf_counter() - start_groq) * 1000.0
            
            parsed = json.loads(ai_res.response)
            success = True
            model_used = ai_res.model
            prompt_tokens = ai_res.prompt_tokens
            completion_tokens = ai_res.completion_tokens
            cost = ai_res.estimated_cost

            # Map generated data
            update_payload = {
                "ai_summary": parsed.get("ai_summary", ""),
                "patient_summary": parsed.get("patient_summary", ""),
                "doctor_summary": parsed.get("doctor_summary", ""),
                "key_findings": parsed.get("key_findings", []),
                "clinical_insights": parsed.get("clinical_insights", []),
                "followup_questions": parsed.get("followup_questions", []),
                "summary_confidence": float(parsed.get("confidence", 0.90)),
                "summary_version": "1.0.0",
                "summary_generated_at": datetime.now(timezone.utc)
            }

        except Exception as err:
            logger.error(f"Structured AI summarization Groq generation failed: {err}. Triggering rule-based fallbacks.", exc_info=True)
            
            # Run local fallback summaries & insights
            fall_summaries = self.summary_service.generate_fallback_summaries(patient_info, labs, risk_findings)
            fall_insights = self.insight_service.generate_fallback_insights(labs, risk_findings, recommendations)
            
            update_payload = {
                "ai_summary": fall_summaries["ai_summary"],
                "patient_summary": fall_summaries["patient_summary"],
                "doctor_summary": fall_summaries["doctor_summary"],
                "key_findings": fall_insights["key_findings"],
                "clinical_insights": fall_insights["clinical_insights"],
                "followup_questions": fall_insights["followup_questions"],
                "summary_confidence": fall_summaries["confidence"],
                "summary_version": "1.0.0-fallback",
                "summary_generated_at": datetime.now(timezone.utc)
            }
            
            latency_ms = (time.time() - start_time) * 1000.0

        # Save to DB
        await self.report_repository.collection.update_one(
            {"_id": self.report_repository.collection.find_one({"_id": report_id}) or report_id},
            {"$set": update_payload}
        )

        # Record telemetry stats
        get_report_ai_telemetry().record_generation(
            model=model_used,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            cost=cost,
            success=success
        )

        return await self.report_repository.get(report_id)
