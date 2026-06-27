"""
Nura - Medical Extraction Validator
"""

import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger("nura.report_extraction.validator")


class ExtractionValidator:
    """Validates types, value formats, units, and empty layouts, generating warning traces"""

    def validate_extracted_data(self, data: Dict[str, Any]) -> List[str]:
        """Perform validation audits on structured medical extraction payloads.
        
        Returns a list of validation warnings. Does NOT raise exceptions.
        """
        warnings = []

        # 1. Validate Patient Info
        patient_info = data.get("patient_information") or {}
        if not patient_info.get("patient_name"):
            warnings.append("Missing required patient name")
        
        age = patient_info.get("age")
        if age is not None:
            try:
                val = int(age)
                if val < 0 or val > 120:
                    warnings.append(f"Patient age value '{age}' is out of realistic clinical bounds (0-120)")
            except (ValueError, TypeError):
                warnings.append(f"Invalid patient age format: {age}")
        else:
            warnings.append("Patient age field is empty")

        dob = patient_info.get("date_of_birth")
        if dob:
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(dob)):
                warnings.append(f"Date of birth '{dob}' does not match standard YYYY-MM-DD format")

        # 2. Validate Hospital Info
        hospital_info = data.get("hospital_information") or {}
        if not hospital_info.get("hospital") and not hospital_info.get("laboratory"):
            warnings.append("Could not identify hospital or laboratory origin details")
            
        rep_date = hospital_info.get("report_date")
        if rep_date:
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(rep_date)):
                warnings.append(f"Report date '{rep_date}' does not match standard YYYY-MM-DD format")
        else:
            warnings.append("Document report date is missing")

        # 3. Validate Laboratory Results
        labs = data.get("laboratory_results") or []
        for idx, lab in enumerate(labs):
            name = lab.get("test_name", f"Index {idx}")
            value = lab.get("value")
            
            if value is None:
                warnings.append(f"Lab test '{name}' has an empty value")
            else:
                # Check if it should be numeric
                try:
                    float(str(value))
                except ValueError:
                    # Non-numeric value is fine for some qualitative tests, but warn if unit is present
                    if lab.get("unit"):
                        warnings.append(f"Qualitative lab test '{name}' value '{value}' is non-numeric but contains unit '{lab.get('unit')}'")

            # Reference range check
            ref_range = lab.get("reference_range")
            if not ref_range:
                warnings.append(f"Lab test '{name}' reference range is missing")

        # 4. Validate Medications
        meds = data.get("medications") or []
        for idx, med in enumerate(meds):
            m_name = med.get("medicine", f"Index {idx}")
            if not med.get("dosage"):
                warnings.append(f"Medication '{m_name}' is missing dosage strength")
            if not med.get("frequency"):
                warnings.append(f"Medication '{m_name}' is missing intake frequency instructions")

        # 5. Empty Sections Checks
        if not labs and not meds:
            warnings.append("Both laboratory results and medications sections are completely empty")
            
        if not data.get("entities") or len(data["entities"]) == 0:
            warnings.append("No medical entities (diagnoses, symptoms, allergies) were extracted from the document")

        return warnings
