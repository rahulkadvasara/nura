"""
Nura - Clinical Risk Assessment Orchestration Service
"""

import time
import logging
from datetime import datetime, timezone
from typing import Optional

from app.models.report import ReportInDB
from app.repositories.report_repository import ReportRepository
from app.services.report_risk.laboratory_analyzer import LaboratoryAnalyzer
from app.services.report_risk.clinical_rules import ClinicalRules
from app.services.report_risk.recommendation_engine import RecommendationEngine
from app.services.report_risk.risk_engine import RiskEngine
from app.services.report_risk.telemetry import get_report_risk_telemetry

logger = logging.getLogger("nura.report_risk.risk_analysis_service")


class RiskAnalysisService:
    """Master service for coordinating laboratory evaluations, clinical rules matches, AI scoring, and MongoDB updates"""

    def __init__(
        self,
        report_repository: ReportRepository,
        lab_analyzer: LaboratoryAnalyzer,
        clinical_rules: ClinicalRules,
        recommendation_engine: RecommendationEngine,
        risk_engine: RiskEngine
    ):
        self.report_repository = report_repository
        self.lab_analyzer = lab_analyzer
        self.clinical_rules = clinical_rules
        self.recommendation_engine = recommendation_engine
        self.risk_engine = risk_engine

    async def analyze_report_risks(self, report_id: str) -> Optional[ReportInDB]:
        """Trigger clinical risk evaluation on a structured report, saving diagnostic flags back to MongoDB"""
        start_time = time.time()
        
        # 1. Fetch report document from MongoDB
        report = await self.report_repository.get(report_id)
        if not report:
            logger.error(f"Report with ID {report_id} not found for clinical risk analysis")
            return None

        # Verify structured extraction exists
        structured_labs = getattr(report, "laboratory_results", []) or []
        medications = getattr(report, "medications", []) or []
        ocr_text = getattr(report, "normalized_text", "") or report.raw_text or ""

        # Set status in DB to processing
        await self.report_repository.collection.update_one(
            {"_id": self.report_repository.collection.find_one({"_id": report_id}) or report_id},
            {"$set": {"processing_status": "processing"}}
        )

        try:
            # 2. Run Laboratory Evaluation
            evaluated_labs = []
            critical_labs_count = 0
            for lab in structured_labs:
                name = lab.get("test_name", "")
                val = lab.get("value")
                unit = lab.get("unit")
                ref_range = lab.get("reference_range")
                
                eval_res = self.lab_analyzer.evaluate_result(name, val, unit, ref_range)
                
                evaluated_labs.append({
                    "test_name": name,
                    "value": val,
                    "unit": unit,
                    "reference_range": ref_range,
                    "status": eval_res["status"],
                    "is_abnormal": eval_res["is_abnormal"],
                    "is_critical": eval_res["is_critical"]
                })
                
                if eval_res["is_critical"]:
                    critical_labs_count += 1

            # Update report laboratory results in DB with analyzed statuses
            if evaluated_labs:
                await self.report_repository.collection.update_one(
                    {"_id": self.report_repository.collection.find_one({"_id": report_id}) or report_id},
                    {"$set": {"laboratory_results": evaluated_labs}}
                )

            # 3. Clinical Rules matches
            rule_findings = self.clinical_rules.evaluate_all(evaluated_labs, medications)

            # 4. Generate structured informational recommendations
            recommendations = self.recommendation_engine.generate_recommendations(rule_findings, critical_labs_count)

            # 5. Risk Scoring and Category mapping
            risk_score, overall_risk = self.risk_engine.calculate_score_and_severity(rule_findings, critical_labs_count)

            # 6. Query AI explanations justifications
            ai_justifications = await self.risk_engine.analyze_risks(ocr_text, rule_findings)
            explanations_map = {
                item["finding_name"].lower(): item["explanation"]
                for item in ai_justifications.get("findings_explanations", [])
                if "finding_name" in item
            }

            # Map diagnostic justifications to findings list
            final_findings = []
            unique_flags = set()
            for f in rule_findings:
                name = f["rule_name"]
                flag = f.get("flag", "CLINICAL_ALERT")
                unique_flags.add(flag)
                
                expl = explanations_map.get(name.lower()) or f.get("message", "Standard clinical rule criteria triggered.")
                
                final_findings.append({
                    "finding_name": name,
                    "severity": f["severity"],
                    "explanation": expl,
                    "flag": flag,
                    "message": f["message"]
                })

            if has_critical_flags := (critical_labs_count > 0):
                unique_flags.add("CRITICAL_LAB")

            # Assemble full risk analysis payload
            risk_analysis_payload = {
                "evaluation_details": {
                    "evaluated_labs_count": len(evaluated_labs),
                    "rule_findings_triggered": len(final_findings),
                    "critical_alerts_count": critical_labs_count
                },
                "metadata": {
                    "confidence_score": ai_justifications.get("confidence", 0.90),
                    "version": "1.0.0"
                }
            }

            # 7. Update MongoDB Report Record
            update_payload = {
                "risk_analysis": risk_analysis_payload,
                "overall_risk": overall_risk,
                "risk_score": risk_score,
                "risk_findings": final_findings,
                "recommendations": recommendations,
                "clinical_flags": list(unique_flags),
                "risk_version": "1.0.0",
                "risk_generated_at": datetime.now(timezone.utc),
                "processing_status": "completed"
            }

            await self.report_repository.collection.update_one(
                {"_id": self.report_repository.collection.find_one({"_id": report_id}) or report_id},
                {"$set": update_payload}
            )

            # Record telemetry stats
            get_report_risk_telemetry().record_analysis(
                severity=overall_risk,
                flags=list(unique_flags),
                recommendations=recommendations,
                success=True
            )

        except Exception as err:
            logger.error(f"Clinical risk assessment pipeline crashed for report {report_id}: {err}", exc_info=True)
            
            await self.report_repository.collection.update_one(
                {"_id": self.report_repository.collection.find_one({"_id": report_id}) or report_id},
                {"$set": {"processing_status": "failed"}}
            )
            
            get_report_risk_telemetry().record_analysis(
                severity="NORMAL",
                flags=[],
                recommendations=[],
                success=False
            )

        return await self.report_repository.get(report_id)
