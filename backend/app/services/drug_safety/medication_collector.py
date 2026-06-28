import logging
from typing import List, Set, Dict, Any, Optional

from app.repositories.prescription_repository import PrescriptionRepository
from app.repositories.reminder_repository import ReminderRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.patient_memory_repository import PatientMemoryRepository
from app.services.drug_safety.normalizer import DrugNormalizer
from app.models.reminder import ReminderType

logger = logging.getLogger("nura.drug_safety.medication_collector")

class MedicationCollector:
    """Collects, normalizes, and deduplicates all medications associated with a patient."""

    def __init__(
        self,
        prescription_repository: PrescriptionRepository,
        reminder_repository: ReminderRepository,
        report_repository: ReportRepository,
        patient_memory_repository: PatientMemoryRepository,
        normalizer: DrugNormalizer
    ):
        self.prescription_repository = prescription_repository
        self.reminder_repository = reminder_repository
        self.report_repository = report_repository
        self.patient_memory_repository = patient_memory_repository
        self.normalizer = normalizer

    async def collect(self, patient_id: str) -> List[str]:
        """
        Collect all medications for a patient from active prescriptions, active reminders,
        report extractions, and patient memory. Returns a list of unique normalized drug names.
        """
        raw_meds: Set[str] = set()

        # 1. Active Prescriptions
        try:
            prescriptions = await self.prescription_repository.get_by_patient_id(patient_id)
            for pres in prescriptions:
                for med in getattr(pres, "medications", []) or []:
                    # med is of type Medication model
                    name = getattr(med, "drug_name", None) or getattr(med, "medicine", None)
                    if name:
                        raw_meds.add(name)
        except Exception as e:
            logger.error(f"Error collecting medications from prescriptions for patient {patient_id}: {e}")

        # 2. Active Reminders
        try:
            reminders = await self.reminder_repository.get_active_reminders(patient_id)
            for rem in reminders:
                if rem.reminder_type == ReminderType.MEDICATION:
                    # Clean title: strip "Take " prefix
                    title = rem.title or ""
                    clean_name = title.strip()
                    if clean_name.lower().startswith("take "):
                        clean_name = clean_name[5:].strip()
                    if clean_name:
                        raw_meds.add(clean_name)
        except Exception as e:
            logger.error(f"Error collecting medications from reminders for patient {patient_id}: {e}")

        # 3. Report Extracted Medications
        try:
            reports = await self.report_repository.get_by_patient_id(patient_id)
            for rep in reports:
                # rep.medications is List[Dict]
                for med in getattr(rep, "medications", []) or []:
                    name = med.get("drug_name") or med.get("medicine")
                    if name:
                        raw_meds.add(name)
        except Exception as e:
            logger.error(f"Error collecting medications from reports for patient {patient_id}: {e}")

        # 4. Patient Memory
        try:
            memory = await self.patient_memory_repository.get_by_patient_id(patient_id)
            if memory:
                for med in getattr(memory, "medications", []) or []:
                    if med:
                        raw_meds.add(med)
                # Also collect from medication_history
                for med_hist in getattr(memory, "medication_history", []) or []:
                    name = med_hist.get("medicine") or med_hist.get("drug_name")
                    if name:
                        raw_meds.add(name)
        except Exception as e:
            logger.error(f"Error collecting medications from patient memory for patient {patient_id}: {e}")

        # Normalize and deduplicate
        normalized_meds: Set[str] = set()
        for raw in raw_meds:
            norm = self.normalizer.normalize(raw)
            if norm:
                normalized_meds.add(norm)

        # Return sorted list for determinism
        return sorted(list(normalized_meds))
