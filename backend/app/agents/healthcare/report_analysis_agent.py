"""
Nura - Report Analysis Agent
Concrete AI Agent for answering grounded questions about medical reports.
"""

import time
from typing import Any, Optional, Dict, List

from app.agents.base.base_agent import BaseAgent
from app.agents.base.context import AgentContext
from app.agents.healthcare.schemas import ReportAnalysisAgentResponse
from app.agents.healthcare.prompts import render_healthcare_prompt
from app.agents.healthcare.telemetry import get_healthcare_agents_telemetry
from app.agents.healthcare.utils import clean_json_response
from app.core.ai_config import ai_settings
from app.services.ai_service import AIService
from app.services.patient_context_service import PatientContextService
from app.agents.retrieval_agent import RetrievalAgent
from app.repositories.report_repository import ReportRepository


class ReportAnalysisAgent(BaseAgent):
    """Production agent explaining medical report findings, abnormal values, and comparisons"""

    def __init__(
        self,
        retrieval_agent: RetrievalAgent,
        patient_context_service: PatientContextService,
        report_repository: ReportRepository,
        ai_service: AIService,
        settings=None
    ):
        super().__init__(name="ReportAnalysisAgent", settings=settings or ai_settings)
        self.retrieval_agent = retrieval_agent
        self.patient_context_service = patient_context_service
        self.report_repository = report_repository
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
        if getattr(context_res, "medical_summary", None):
            parts.append(f"Medical Summary: {context_res.medical_summary}")
        if getattr(context_res, "current_conditions", None):
            parts.append(f"Chronic Conditions: {', '.join(context_res.current_conditions)}")
        if getattr(context_res, "medication_allergies", None):
            parts.append(f"Allergies: {', '.join(context_res.medication_allergies)}")
        return "\n".join(parts) if parts else "No patient context available."

    async def execute(self, input_data: Any, context: Optional[AgentContext] = None) -> Any:
        """
        Execute Report Analysis pipeline:
        - Query Qdrant via RetrievalAgent
        - Compile patient history from MongoDB
        - Query MongoDB reports collection for metadata list
        - Render prompt
        - Call Groq in structured JSON format
        - Parse outcomes and enforce safety disclosures
        """
        query = str(input_data).strip()
        patient_id = context.patient_id if context else None
        
        start_time = time.perf_counter()
        retrieval_start = time.perf_counter()
        
        # 1. Query Qdrant retrieval contexts (Force intent to report_analysis)
        retrieval_ctx = context.model_copy(update={
            "metadata": {
                **(context.metadata or {}),
                "intent": "report_analysis"
            }
        }) if context else AgentContext(metadata={"intent": "report_analysis"})

        retrieval_res = await self.retrieval_agent.run(query, retrieval_ctx)
        retrieval_latency = (time.perf_counter() - retrieval_start) * 1000.0
        
        retrieval_data = retrieval_res.response or {}
        retrieved_context = retrieval_data.get("context", "")
        citations_raw = retrieval_data.get("retrieved_chunks", [])
        
        citations = []
        for c in citations_raw:
            citations.append({
                "source": c.get("metadata", {}).get("source", "patient_reports"),
                "text": c.get("text", "")[:200] + "...",
                "score": c.get("score", 0.0),
                "document_id": c.get("metadata", {}).get("document_id")
            })

        # 2. Query patient context details
        patient_context_str = "No patient context available."
        if patient_id:
            try:
                patient_context_res = await self.patient_context_service.assemble_context(patient_id)
                patient_context_str = self._format_patient_context(patient_context_res)
            except Exception as e:
                self.logger.warning(f"Failed to assemble patient context: {str(e)}")

        # 3. Fetch list of recent medical reports metadata from DB
        reports_meta_str = "No medical reports metadata available."
        if patient_id:
            try:
                reports = await self.report_repository.get_by_patient_id(patient_id, limit=20)
                if reports:
                    parts = []
                    for r in reports:
                        r_id = getattr(r, "id", str(getattr(r, "_id", "")))
                        parts.append(
                            f"ID: {r_id} | Type: {r.report_type} | "
                            f"Uploaded At: {r.created_at.isoformat() if r.created_at else 'Unknown'} | "
                            f"Risk Level: {r.risk_level} | "
                            f"Summary: {r.ai_summary or 'No summary'}"
                        )
                    reports_meta_str = "\n".join(parts)
            except Exception as e:
                self.logger.warning(f"Failed to fetch report metadata from DB: {str(e)}")

        # 4. Formulate prompts
        try:
            rendered_system = render_healthcare_prompt("report_analysis_system", {}, is_system=True)
            rendered_user = render_healthcare_prompt("report_analysis_user", {
                "patient_context": patient_context_str,
                "retrieved_context": f"Report Metadata:\n{reports_meta_str}\n\nReport Contents:\n{retrieved_context or 'No report content reference text retrieved.'}",
                "query": query
            })
        except Exception as e:
            self.logger.error(f"Failed to render report templates: {str(e)}")
            rendered_system = "You are a clinical report analysis agent. Return valid JSON containing summary, key_findings, abnormal_values, trend_analysis, and recommendations."
            rendered_user = f"Context:\n{retrieved_context}\n\nMetadata:\n{reports_meta_str}\n\nQuery: {query}"

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
        
        summary = parsed_json.get("summary", "Report analysis completed.")
        key_findings = parsed_json.get("key_findings", [])
        abnormal_values = parsed_json.get("abnormal_values", [])
        trend_analysis = parsed_json.get("trend_analysis", [])
        recommendations = parsed_json.get("recommendations", ["Please consult your physician to discuss these findings."])

        agent_res = ReportAnalysisAgentResponse(
            summary=summary,
            key_findings=key_findings,
            abnormal_values=abnormal_values,
            trend_analysis=trend_analysis,
            recommendations=recommendations,
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
            citation_count=len(citations)
        )
        
        return agent_res
