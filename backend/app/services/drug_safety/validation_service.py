import time
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.drug_safety.medication_collector import MedicationCollector
from app.services.drug_safety.decision_engine import ValidationDecisionEngine
from app.services.drug_safety.telemetry import drug_safety_telemetry
from app.services.drug_safety.interaction_engine import DrugInteractionEngine

logger = logging.getLogger("nura.drug_safety.validation_service")

class MedicationValidationService:
    """Coordinating service that aggregates current patient medications and runs validation rules."""

    def __init__(
        self,
        database: AsyncIOMotorDatabase,
        collector: MedicationCollector,
        decision_engine: ValidationDecisionEngine,
        interaction_engine: DrugInteractionEngine
    ):
        self.db = database
        self.patient_memory_col = database.patient_memory
        self.collector = collector
        self.decision_engine = decision_engine
        self.interaction_engine = interaction_engine

    async def validate_medications(
        self,
        patient_id: str,
        incoming_medications: List[str],
        source: str = "api"
    ) -> Dict[str, Any]:
        """
        Validate incoming medications against a patient's existing medication profile.
        Updates telemetry according to the source and returned decision.
        """
        start_time = time.perf_counter()

        try:
            # Collect current normalized medications
            current_normalized = await self.collector.collect(patient_id)
            
            # Evaluate using decision engine
            result = await self.decision_engine.evaluate(current_normalized, incoming_medications)
            
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            
            # Record telemetry
            drug_safety_telemetry.record_validation(
                source=source,
                decision=result["decision"],
                latency_ms=latency_ms
            )

            result["latency_ms"] = round(latency_ms, 2)
            result["collected_medications"] = current_normalized
            return result

        except Exception as e:
            logger.error(f"Error executing medication validation for patient {patient_id}: {e}", exc_info=True)
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            drug_safety_telemetry.record_validation(
                source=source,
                decision="BLOCK",
                latency_ms=latency_ms
            )
            raise e

    async def validate_and_update_patient_memory(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """
        Collect all current medications, run interaction checks on the full set,
        and update the validation_summary nested object inside patient_memory in MongoDB.
        """
        start_time = time.perf_counter()
        
        try:
            # Collect current normalized medications
            current_normalized = await self.collector.collect(patient_id)
            
            # Fetch existing patient memory to update historical values
            existing = await self.patient_memory_col.find_one({"patient_id": patient_id})
            
            prev_validation_summaries = []
            interaction_history = []
            highest_historical_severity = "NONE"
            
            if existing:
                prev_validation_summaries = existing.get("previous_validation_summaries") or []
                interaction_history = existing.get("interaction_history") or []
                highest_historical_severity = existing.get("highest_historical_severity") or "NONE"
                
                # Push the current validation_summary if it exists to prev_validation_summaries
                old_summary = existing.get("validation_summary")
                if old_summary:
                    prev_validation_summaries.append(old_summary)
                    prev_validation_summaries = prev_validation_summaries[-20:]

            # If 0 or 1 medications, there can be no interactions, overall severity is NONE
            if len(current_normalized) <= 1:
                summary_dict = {
                    "active_medications": current_normalized,
                    "interaction_findings": [],
                    "overall_severity": "NONE",
                    "validation_timestamp": datetime.now(timezone.utc).isoformat(),
                    "summary": "No known interactions detected.",
                    "latest_validation_date": datetime.now(timezone.utc).isoformat(),
                    "active_interaction_count": 0,
                    "highest_severity": "NONE",
                    "interaction_summary": "No known interactions detected."
                }
            else:
                # Run complete interaction check on all current medications
                check_res = await self.interaction_engine.check_interactions(current_normalized)
                
                findings = [
                    {
                        "drug_a": inter.drug_a,
                        "drug_b": inter.drug_b,
                        "drug_a_normalized": inter.drug_a_normalized,
                        "drug_b_normalized": inter.drug_b_normalized,
                        "severity": inter.severity,
                        "description": inter.description
                    } for inter in check_res.detected_interactions
                ]
                
                summary_dict = {
                    "active_medications": current_normalized,
                    "interaction_findings": findings,
                    "overall_severity": check_res.severity,
                    "validation_timestamp": datetime.now(timezone.utc).isoformat(),
                    "summary": (
                        f"Detected {len(findings)} interaction(s). "
                        f"Highest severity: {check_res.severity}."
                    ) if len(findings) > 0 else "No known interactions detected.",
                    "latest_validation_date": datetime.now(timezone.utc).isoformat(),
                    "active_interaction_count": len(findings),
                    "highest_severity": check_res.severity,
                    "interaction_summary": (
                        f"Detected {len(findings)} interaction(s). "
                        f"Highest severity: {check_res.severity}."
                    ) if len(findings) > 0 else "No known interactions detected."
                }

            # Update highest historical severity
            weights = {"NONE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
            new_weight = weights.get(summary_dict["overall_severity"].upper(), 0)
            old_weight = weights.get(highest_historical_severity.upper(), 0)
            if new_weight > old_weight:
                highest_historical_severity = summary_dict["overall_severity"]

            # Log to interaction_history
            interaction_history.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "active_medications": current_normalized,
                "overall_severity": summary_dict["overall_severity"],
                "active_interaction_count": summary_dict["active_interaction_count"]
            })
            interaction_history = interaction_history[-50:]

            # Update patient memory document directly
            # If the document does not exist, we upsert a basic one
            await self.patient_memory_col.update_one(
                {"patient_id": patient_id},
                {
                    "$set": {
                        "validation_summary": summary_dict,
                        "medications": current_normalized,
                        "previous_validation_summaries": prev_validation_summaries,
                        "interaction_history": interaction_history,
                        "highest_historical_severity": highest_historical_severity,
                        "latest_validation_timestamp": datetime.now(timezone.utc),
                        "last_updated": datetime.now(timezone.utc)
                    },
                    "$setOnInsert": {
                        "ai_summary": "Initial baseline context."
                    }
                },
                upsert=True
            )

            latency_ms = (time.perf_counter() - start_time) * 1000.0
            drug_safety_telemetry.record_validation(
                source="patient_memory",
                decision="ALLOW" if summary_dict["active_interaction_count"] == 0 else "WARNING",
                latency_ms=latency_ms
            )

            return summary_dict

        except Exception as e:
            logger.error(f"Failed to update patient memory validation summary for patient {patient_id}: {e}", exc_info=True)
            return None
