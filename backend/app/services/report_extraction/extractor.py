"""
Nura - Medical Information Extraction Service
"""

import time
import logging
from typing import Optional, Dict, Any

from app.models.report import ReportInDB, ReportUpdate
from app.repositories.report_repository import ReportRepository
from app.services.report_extraction.document_classifier import DocumentClassifier
from app.services.report_extraction.medical_entity_extractor import MedicalEntityExtractor
from app.services.report_extraction.laboratory_parser import LaboratoryParser
from app.services.report_extraction.medication_parser import MedicationParser
from app.services.report_extraction.normalizer import MedicalNormalizer
from app.services.report_extraction.validator import ExtractionValidator
from app.services.report_extraction.telemetry import get_report_extraction_telemetry

logger = logging.getLogger("nura.report_extraction.extractor")


class ReportExtractionService:
    """Master orchestrator for document classification, medical entity extraction, normalizations, and updates"""

    def __init__(
        self,
        report_repository: ReportRepository,
        classifier: DocumentClassifier,
        entity_extractor: MedicalEntityExtractor,
        lab_parser: LaboratoryParser,
        med_parser: MedicationParser,
        normalizer: MedicalNormalizer,
        validator: ExtractionValidator,
    ):
        self.report_repository = report_repository
        self.classifier = classifier
        self.entity_extractor = entity_extractor
        self.lab_parser = lab_parser
        self.med_parser = med_parser
        self.normalizer = normalizer
        self.validator = validator

    async def extract_medical_information(self, report_id: str) -> Optional[ReportInDB]:
        """Runs the extraction pipeline for a report record by ID, saving outputs back to MongoDB"""
        start_time = time.time()
        
        # 1. Fetch report document record
        report = await self.report_repository.get(report_id)
        if not report:
            logger.error(f"Report with ID {report_id} not found for medical extraction")
            return None

        # Verify OCR completed before starting extraction
        ocr_text = getattr(report, "normalized_text", None) or report.raw_text
        if not ocr_text:
            logger.warning(f"Report {report_id} contains no OCR text. Extraction skipped.")
            return report

        # Update extraction status to processing
        await self.report_repository.collection.update_one(
            {"_id": self.report_repository.collection.find_one({"_id": report_id}) or report_id},
            {"$set": {"extraction_status": "processing"}}
        )

        try:
            # 2. Document Classification
            class_res = await self.classifier.classify(ocr_text)
            doc_type = class_res["document_type"]

            # 3. Medical Entity Extraction (patient info, clinic info, entities)
            entity_res = await self.entity_extractor.extract_entities(ocr_text)
            
            # Normalize demographic / hospital details
            patient_info = entity_res["patient_information"]
            if "date_of_birth" in patient_info:
                patient_info["date_of_birth"] = self.normalizer.normalize_date(patient_info["date_of_birth"])
                
            hospital_info = entity_res["hospital_information"]
            if "report_date" in hospital_info:
                hospital_info["report_date"] = self.normalizer.normalize_date(hospital_info["report_date"])

            # 4. Lab Results Parsing (Blood test types only)
            labs = []
            if doc_type in ("Blood Test", "CBC", "Liver Function", "Kidney Function", "Lipid Profile", "Diabetes", "Thyroid", "Urine"):
                labs = await self.lab_parser.parse_labs(ocr_text)
                # Normalize lab test entries
                for lab in labs:
                    lab["unit"] = self.normalizer.normalize_unit(lab.get("unit"))
                    lab["status"] = self.normalizer.normalize_status(lab.get("status"))

            # 5. Medications Prescription Parsing
            meds = []
            if doc_type in ("Prescription", "Discharge Summary", "Consultation Note"):
                meds = await self.med_parser.parse_medications(ocr_text)

            # 6. Extract Diagnoses and Allergies lists from general entities
            diagnoses_list = []
            allergies_list = []
            for ent in entity_res.get("entities", []):
                cat = ent.get("category", "").lower()
                text = ent.get("text", "").strip()
                if not text:
                    continue
                if cat in ("diagnoses", "diseases"):
                    diagnoses_list.append(text)
                elif cat == "allergies":
                    allergies_list.append(text)

            # Consolidate and merge duplicates
            diagnoses_list = self.normalizer.merge_diagnoses(diagnoses_list)
            allergies_list = self.normalizer.merge_allergies(allergies_list)

            # Assemble full structured data dictionary
            structured_data = {
                "patient_information": patient_info,
                "hospital_information": hospital_info,
                "metadata": {
                    "extraction_method": entity_res["method"],
                    "extraction_version": "1.0.0",
                    "confidence_score": entity_res["confidence"]
                }
            }

            # 7. Pipeline sanity checks validation
            warnings = self.validator.validate_extracted_data({
                "patient_information": patient_info,
                "hospital_information": hospital_info,
                "laboratory_results": labs,
                "medications": meds,
                "entities": entity_res.get("entities", [])
            })

            duration_ms = (time.time() - start_time) * 1000.0
            avg_confidence = (class_res["confidence"] + entity_res["confidence"]) / 2.0

            # 8. Save structured results back to MongoDB Report record
            update_payload = {
                "document_type": doc_type,
                "structured_data": structured_data,
                "entities": entity_res.get("entities", []),
                "laboratory_results": labs,
                "medications": meds,
                "diagnoses": diagnoses_list,
                "allergies": allergies_list,
                "extraction_status": "completed",
                "extraction_confidence": avg_confidence,
                "extraction_version": "1.0.0",
                "extraction_warnings": warnings
            }

            await self.report_repository.collection.update_one(
                {"_id": self.report_repository.collection.find_one({"_id": report_id}) or report_id},
                {"$set": update_payload}
            )

            # Log telemetry stats
            get_report_extraction_telemetry().record_extraction(
                doc_type=doc_type,
                confidence=avg_confidence,
                duration_ms=duration_ms,
                success=True
            )

        except Exception as err:
            logger.error(f"Structured extraction pipeline crashed for report {report_id}: {err}", exc_info=True)
            duration_ms = (time.time() - start_time) * 1000.0
            
            await self.report_repository.collection.update_one(
                {"_id": self.report_repository.collection.find_one({"_id": report_id}) or report_id},
                {
                    "$set": {
                        "extraction_status": "failed",
                        "extraction_warnings": [f"Pipeline crash: {str(err)}"]
                    }
                }
            )
            
            get_report_extraction_telemetry().record_extraction(
                doc_type="Other",
                confidence=0.0,
                duration_ms=duration_ms,
                success=False
            )

        return await self.report_repository.get(report_id)
