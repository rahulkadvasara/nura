"""
Nura - Medical Entity Extractor
"""

import json
import logging
import re
from typing import Dict, List, Any
from app.services.ai_service import AIService

logger = logging.getLogger("nura.report_extraction.medical_entity_extractor")


class MedicalEntityExtractor:
    """Extracts demographic data, hospital records, and medical entity arrays from OCR text"""

    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service

    async def extract_entities(self, ocr_text: str) -> Dict[str, Any]:
        """Extract patient, hospital info, and general clinical entities.
        
        Returns dict containing:
        - patient_information: Dict
        - hospital_information: Dict
        - entities: List[Dict]
        - confidence: float
        - method: str
        """
        if not ocr_text or len(ocr_text.strip()) == 0:
            return self._get_empty_result("rule_fallback")

        # 1. Attempt LLM extraction
        try:
            system_prompt = (
                "You are an expert clinical information extractor. Analyze the provided medical report "
                "and extract patient information, hospital/laboratory details, and any medical entities.\n\n"
                "Medical entities categories include: Diagnoses, Symptoms, Diseases, Allergies, Procedures, "
                "Medications, Surgeries, Vaccinations, Family History.\n\n"
                "Respond ONLY with a valid JSON object matching this schema:\n"
                "{\n"
                '  "patient_information": {\n'
                '    "patient_name": "string or null",\n'
                '    "age": "integer or null",\n'
                '    "gender": "string or null",\n'
                '    "date_of_birth": "string YYYY-MM-DD or null",\n'
                '    "patient_id": "string or null"\n'
                "  },\n"
                '  "hospital_information": {\n'
                '    "hospital": "string or null",\n'
                '    "laboratory": "string or null",\n'
                '    "doctor": "string or null",\n'
                '    "department": "string or null",\n'
                '    "report_date": "string YYYY-MM-DD or null"\n'
                "  },\n"
                '  "entities": [\n'
                "    {\n"
                '      "text": "string (original text value)",\n'
                '      "category": "string (lowercase category: diagnoses, symptoms, diseases, allergies, procedures, medications, surgeries, vaccinations, family_history)",\n'
                '      "confidence": 0.95,\n'
                '      "page": 1,\n'
                '      "position": "string or null"\n'
                "    }\n"
                "  ],\n"
                '  "confidence": 0.95\n'
                "}"
            )
            
            res = await self.ai_service.generate_json(
                prompt=f"OCR Text:\n\n{ocr_text[:4000]}",
                system_prompt=system_prompt,
                temperature=0.0
            )
            
            parsed = json.loads(res.response)
            return {
                "patient_information": parsed.get("patient_information") or {},
                "hospital_information": parsed.get("hospital_information") or {},
                "entities": parsed.get("entities") or [],
                "confidence": float(parsed.get("confidence", 0.9)),
                "method": "llm_groq"
            }
        except Exception as e:
            logger.warning(f"LLM entity extraction failed or invalid: {e}. Executing local fallback rules.")

        # 2. Local Regex/Keyword heuristic fallback extraction
        return self._extract_fallback(ocr_text)

    def _get_empty_result(self, method: str) -> Dict[str, Any]:
        return {
            "patient_information": {
                "patient_name": None,
                "age": None,
                "gender": None,
                "date_of_birth": None,
                "patient_id": None
            },
            "hospital_information": {
                "hospital": None,
                "laboratory": None,
                "doctor": None,
                "department": None,
                "report_date": None
            },
            "entities": [],
            "confidence": 0.50,
            "method": method
        }

    def _extract_fallback(self, ocr_text: str) -> Dict[str, Any]:
        res = self._get_empty_result("rule_fallback")
        text_lower = ocr_text.lower()

        # Simple regex extracts
        # Patient Name
        name_match = re.search(r"(?:patient name|name)\s*:\s*([a-zA-Z ]+)", ocr_text, re.IGNORECASE)
        if name_match:
            res["patient_information"]["patient_name"] = name_match.group(1).strip()
            
        # Age
        age_match = re.search(r"age\s*:\s*(\d+)", ocr_text, re.IGNORECASE)
        if age_match:
            try:
                res["patient_information"]["age"] = int(age_match.group(1).strip())
            except ValueError:
                pass
                
        # Gender
        gender_match = re.search(r"(?:gender|sex)\s*:\s*(male|female|m|f|other)", ocr_text, re.IGNORECASE)
        if gender_match:
            g = gender_match.group(1).strip().lower()
            res["patient_information"]["gender"] = "Male" if g in ("male", "m") else "Female" if g in ("female", "f") else "Other"

        # Report Date
        date_match = re.search(r"(?:report date|date)\s*:\s*([\d\-\/a-zA-Z ]+)", ocr_text, re.IGNORECASE)
        if date_match:
            res["hospital_information"]["report_date"] = date_match.group(1).strip()

        # Extract basic medical entities (diagnoses and symptoms keywords)
        diagnoses_keywords = ["diabetes", "hypertension", "fatigue", "cholesterol", "anemia", "thyroiditis"]
        for kw in diagnoses_keywords:
            if kw in text_lower:
                res["entities"].append({
                    "text": kw.capitalize(),
                    "category": "diagnoses" if kw != "fatigue" else "symptoms",
                    "confidence": 0.80,
                    "page": 1,
                    "position": "text_match"
                })

        return res
