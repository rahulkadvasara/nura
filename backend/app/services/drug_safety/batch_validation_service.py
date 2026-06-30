import asyncio
import logging
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.services.drug_safety.validation_service import MedicationValidationService

logger = logging.getLogger("nura.drug_safety.batch_validation")

class BatchValidationService:
    """
    Engine to support parallel validation of medication lists, reports, and patient memory updates.
    Enforces bounded concurrency via a semaphore and de-duplicates queries.
    """

    def __init__(
        self,
        database: AsyncIOMotorDatabase,
        validation_service: MedicationValidationService,
        max_concurrency: int = 5
    ):
        self.db = database
        self.validation_service = validation_service
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def validate_medication_lists(
        self,
        patient_id: str,
        medication_lists: List[List[str]],
        source: str = "batch"
    ) -> List[Dict[str, Any]]:
        """
        Validate multiple medication lists for a single patient, de-duplicating lists to avoid redundant lookups.
        """
        if not medication_lists:
            return []

        # De-duplicate lists to validate (sort and serialize each list to form a unique key)
        unique_lists = []
        seen_keys = set()
        for idx, med_list in enumerate(medication_lists):
            cleaned = sorted([m.strip().upper() for m in med_list if m and m.strip()])
            key = tuple(cleaned)
            if key not in seen_keys:
                seen_keys.add(key)
                unique_lists.append((key, med_list, idx))

        results_map = {}

        async def _validate_with_semaphore(key, med_list, original_index):
            async with self.semaphore:
                try:
                    res = await self.validation_service.validate_medications(
                        patient_id=patient_id,
                        incoming_medications=med_list,
                        source=source
                    )
                    results_map[key] = {"success": True, "data": res}
                except Exception as e:
                    logger.error(f"Batch item validation failed: {e}")
                    results_map[key] = {"success": False, "error": str(e)}

        tasks = [_validate_with_semaphore(key, ml, idx) for key, ml, idx in unique_lists]
        await asyncio.gather(*tasks)

        # Assemble final results keeping original ordering
        final_results = []
        for med_list in medication_lists:
            cleaned = sorted([m.strip().upper() for m in med_list if m and m.strip()])
            key = tuple(cleaned)
            final_results.append(results_map.get(key, {"success": False, "error": "Validation skipped or failed"}))

        return final_results

    async def validate_report_imports(
        self,
        patient_id: str,
        reports_medications: List[List[str]]
    ) -> List[Dict[str, Any]]:
        """
        Validate extracted medication lists from a batch of imported reports.
        """
        return await self.validate_medication_lists(
            patient_id=patient_id,
            medication_lists=reports_medications,
            source="report_batch"
        )

    async def validate_patient_historical(self, patient_ids: List[str]) -> Dict[str, Any]:
        """
        Trigger historical validation updates across a collection of patients in parallel.
        De-duplicates patient IDs.
        """
        if not patient_ids:
            return {
                "success": True,
                "total_requested": 0,
                "total_unique": 0,
                "success_count": 0,
                "failed_count": 0,
                "results": {}
            }

        unique_pids = list(set(patient_ids))
        results_map = {}
        success_count = 0
        failed_count = 0

        async def _validate_patient(pid):
            nonlocal success_count, failed_count
            async with self.semaphore:
                try:
                    res = await self.validation_service.validate_and_update_patient_memory(pid)
                    if res is not None:
                        results_map[pid] = {"success": True, "summary": res}
                        success_count += 1
                    else:
                        results_map[pid] = {"success": False, "error": "Returned empty result summary"}
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Failed historical validation update for patient {pid}: {e}")
                    results_map[pid] = {"success": False, "error": str(e)}
                    failed_count += 1

        tasks = [_validate_patient(pid) for pid in unique_pids]
        await asyncio.gather(*tasks)

        return {
            "success": True,
            "total_requested": len(patient_ids),
            "total_unique": len(unique_pids),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results_map
        }
