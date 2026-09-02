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
        report extractions, and patient memory without double-counting across sources.
        """
        collected_normalized: List[str] = []
        seen_primary_norms: Set[str] = set()

        # 1. Active Reminders (Primary source for reminders)
        try:
            reminders = await self.reminder_repository.get_active_reminders(patient_id)
            for rem in reminders:
                if rem.reminder_type == ReminderType.MEDICATION:
                    title = rem.title or ""
                    clean_name = title.strip()
                    if clean_name.lower().startswith("take "):
                        clean_name = clean_name[5:].strip()
                    if clean_name:
                        norm = self.normalizer.normalize(clean_name)
                        if norm:
                            collected_normalized.append(norm)
                            seen_primary_norms.add(norm)
        except Exception as e:
            logger.error(f"Error collecting medications from reminders for patient {patient_id}: {e}")

        # 2. Active Prescriptions (Only add if not already present in active reminders)
        try:
            prescriptions = await self.prescription_repository.get_by_patient_id(patient_id)
            for pres in prescriptions:
                for med in getattr(pres, "medications", []) or []:
                    name = getattr(med, "drug_name", None) or getattr(med, "medicine", None)
                    if name:
                        norm = self.normalizer.normalize(name)
                        if norm and norm not in seen_primary_norms:
                            collected_normalized.append(norm)
                            seen_primary_norms.add(norm)
        except Exception as e:
            logger.error(f"Error collecting medications from prescriptions for patient {patient_id}: {e}")

        # 3. Report Extracted Medications (Only add if not already present in reminders/prescriptions)
        try:
            reports = await self.report_repository.get_by_patient_id(patient_id)
            for rep in reports:
                for med in getattr(rep, "medications", []) or []:
                    name = med.get("drug_name") or med.get("medicine")
                    if name:
                        norm = self.normalizer.normalize(name)
                        if norm and norm not in seen_primary_norms:
                            collected_normalized.append(norm)
                            seen_primary_norms.add(norm)
        except Exception as e:
            logger.error(f"Error collecting medications from reports for patient {patient_id}: {e}")

        # 4. Patient Memory (Only add if not already present in reminders/prescriptions/reports)
        try:
            memory = await self.patient_memory_repository.get_by_patient_id(patient_id)
            if memory:
                for med in getattr(memory, "medications", []) or []:
                    if med:
                        norm = self.normalizer.normalize(med)
                        if norm and norm not in seen_primary_norms:
                            collected_normalized.append(norm)
                            seen_primary_norms.add(norm)
        except Exception as e:
            logger.error(f"Error collecting medications from patient memory for patient {patient_id}: {e}")

        return collected_normalized
