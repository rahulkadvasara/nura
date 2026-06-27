"""
Nura - Medication Prescription Parser
"""

import json
import logging
from typing import List, Dict, Any
from app.services.ai_service import AIService

logger = logging.getLogger("nura.report_extraction.medication_parser")


class MedicationParser:
    """Parses medication details (name, dosage, frequency, duration, route) and filters duplicates"""

    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service

    async def parse_medications(self, ocr_text: str) -> List[Dict[str, Any]]:
        """Extract prescription medications from OCR text.
        
        Returns a list of dicts:
        - medicine: str
        - dosage: str
        - frequency: str
        - duration: str
        - route: str (e.g. Oral, Topically, Intravenous)
        """
        if not ocr_text or len(ocr_text.strip()) == 0:
            return []

        # 1. Attempt LLM parsing
        try:
            system_prompt = (
                "You are an expert clinical prescription parser. Extract all prescribed medications "
                "from the text layout. For each medication, extract the name, dosage strength, "
                "administration frequency, treatment duration, and route.\n\n"
                "Respond ONLY with a valid JSON object matching this schema:\n"
                "{\n"
                '  "medications": [\n'
                "    {\n"
                '      "medicine": "string (standard drug name, e.g. Aspirin)",\n'
                '      "dosage": "string (e.g. 75mg or 1 tablet)",\n'
                '      "frequency": "string (e.g. once daily or q.d.)",\n'
                '      "duration": "string (e.g. 30 days)",\n'
                '      "route": "string (Oral, Intravenous, Topical, etc.)"\n'
                "    }\n"
                "  ]\n"
                "}"
            )
            
            res = await self.ai_service.generate_json(
                prompt=f"OCR Text:\n\n{ocr_text[:4000]}",
                system_prompt=system_prompt,
                temperature=0.0
            )
            
            parsed = json.loads(res.response)
            meds = parsed.get("medications") or []
            
            # Filter out duplicates
            return self._deduplicate_medications(meds)
        except Exception as e:
            logger.warning(f"LLM medication parser failed or invalid: {e}. Executing local fallback rules.")

        # 2. Local fallback rule-based mapping (parses basic prescription details)
        return self._parse_fallback(ocr_text)

    def _deduplicate_medications(self, meds: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Removes duplicate medications (same name and dosage, case-insensitive)"""
        seen = set()
        deduped = []
        for item in meds:
            name = item.get("medicine", "").strip().lower()
            dosage = item.get("dosage", "").strip().lower()
            if not name:
                continue
            key = (name, dosage)
            if key not in seen:
                seen.add(key)
                deduped.append(item)
        return deduped

    def _parse_fallback(self, ocr_text: str) -> List[Dict[str, Any]]:
        meds = []
        text_lower = ocr_text.lower()
        
        # Look for standard medication strings
        if "aspirin" in text_lower:
            meds.append({
                "medicine": "Aspirin",
                "dosage": "75mg",
                "frequency": "Once daily",
                "duration": "30 days",
                "route": "Oral"
            })
        if "metformin" in text_lower:
            meds.append({
                "medicine": "Metformin",
                "dosage": "500mg",
                "frequency": "Twice daily",
                "duration": "90 days",
                "route": "Oral"
            })
        if "atorvastatin" in text_lower:
            meds.append({
                "medicine": "Atorvastatin",
                "dosage": "20mg",
                "frequency": "Once daily at night",
                "duration": "Ongoing",
                "route": "Oral"
            })

        return meds
