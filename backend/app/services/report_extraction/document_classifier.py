"""
Nura - Medical Document Classifier
"""

import json
import logging
from typing import Dict, Any
from app.services.ai_service import AIService

logger = logging.getLogger("nura.report_extraction.document_classifier")


class DocumentClassifier:
    """Classifies unstructured OCR text content into clinical document types"""

    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service

    async def classify(self, ocr_text: str) -> Dict[str, Any]:
        """Classify OCR text.
        
        Returns dict containing:
        - document_type: str
        - confidence: float
        - method: str
        """
        if not ocr_text or len(ocr_text.strip()) == 0:
            return {
                "document_type": "Other",
                "confidence": 1.0,
                "method": "rule_fallback"
            }

        # 1. Attempt LLM classification
        try:
            system_prompt = (
                "You are an expert clinical documentation classifier. Classify the provided medical report "
                "into precisely one of the following categories:\n"
                "- Blood Test\n- CBC\n- Liver Function\n- Kidney Function\n- Lipid Profile\n- Diabetes\n"
                "- Thyroid\n- Urine\n- Prescription\n- Radiology\n- Discharge Summary\n- Consultation Note\n- Other\n\n"
                "Respond ONLY with a valid JSON object matching this schema:\n"
                '{"document_type": "<selected_category>", "confidence": <float_score_between_0_and_1>}'
            )
            
            res = await self.ai_service.generate_json(
                prompt=f"OCR Text:\n\n{ocr_text[:3000]}",
                system_prompt=system_prompt,
                temperature=0.0
            )
            
            parsed = json.loads(res.response)
            doc_type = parsed.get("document_type", "Other")
            confidence = parsed.get("confidence", 0.9)
            
            # Map/Sanity check output category
            allowed = {
                "blood test", "cbc", "liver function", "kidney function", "lipid profile", "diabetes",
                "thyroid", "urine", "prescription", "radiology", "discharge summary", "consultation note", "other"
            }
            if doc_type.lower() in allowed:
                # Keep exact case formatting
                formatted_types = {
                    "blood test": "Blood Test",
                    "cbc": "CBC",
                    "liver function": "Liver Function",
                    "kidney function": "Kidney Function",
                    "lipid profile": "Lipid Profile",
                    "diabetes": "Diabetes",
                    "thyroid": "Thyroid",
                    "urine": "Urine",
                    "prescription": "Prescription",
                    "radiology": "Radiology",
                    "discharge summary": "Discharge Summary",
                    "consultation note": "Consultation Note",
                    "other": "Other"
                }
                return {
                    "document_type": formatted_types[doc_type.lower()],
                    "confidence": float(confidence),
                    "method": "llm_groq"
                }
        except Exception as e:
            logger.warning(f"LLM classification request failed or invalid: {e}. Running local keyword heuristics.")

        # 2. Local rule-based keyword fallback mapping
        text_lower = ocr_text.lower()
        if "prescription" in text_lower or "rx" in text_lower or "take 1 tablet" in text_lower or "dosage:" in text_lower:
            return {"document_type": "Prescription", "confidence": 0.85, "method": "rule_fallback"}
        if "lipid" in text_lower or "cholesterol" in text_lower or "triglyceride" in text_lower or "ldl" in text_lower:
            return {"document_type": "Lipid Profile", "confidence": 0.85, "method": "rule_fallback"}
        if "liver" in text_lower or "bilirubin" in text_lower or "sgot" in text_lower or "sgpt" in text_lower or "alt" in text_lower:
            return {"document_type": "Liver Function", "confidence": 0.85, "method": "rule_fallback"}
        if "kidney" in text_lower or "creatinine" in text_lower or "urea" in text_lower or "egfr" in text_lower:
            return {"document_type": "Kidney Function", "confidence": 0.85, "method": "rule_fallback"}
        if "glucose" in text_lower or "hba1c" in text_lower or "diabetes" in text_lower or "insulin" in text_lower:
            return {"document_type": "Diabetes", "confidence": 0.85, "method": "rule_fallback"}
        if "thyroid" in text_lower or "tsh" in text_lower or "t3" in text_lower or "t4" in text_lower:
            return {"document_type": "Thyroid", "confidence": 0.85, "method": "rule_fallback"}
        if "urine" in text_lower or "microscopy" in text_lower or "leukocytes" in text_lower or "specific gravity" in text_lower:
            return {"document_type": "Urine", "confidence": 0.85, "method": "rule_fallback"}
        if "cbc" in text_lower or "hemoglobin" in text_lower or "wbc" in text_lower or "rbc" in text_lower or "platelet" in text_lower:
            return {"document_type": "CBC", "confidence": 0.85, "method": "rule_fallback"}
        if "x-ray" in text_lower or "mri" in text_lower or "ct scan" in text_lower or "ultrasound" in text_lower or "radiology" in text_lower:
            return {"document_type": "Radiology", "confidence": 0.85, "method": "rule_fallback"}
        if "discharge summary" in text_lower or "history of present illness" in text_lower or "hospital course" in text_lower:
            return {"document_type": "Discharge Summary", "confidence": 0.85, "method": "rule_fallback"}
        if "consultation note" in text_lower or "subjective:" in text_lower or "objective:" in text_lower or "soap note" in text_lower:
            return {"document_type": "Consultation Note", "confidence": 0.80, "method": "rule_fallback"}
        if "blood test" in text_lower or "hematology" in text_lower or "serology" in text_lower:
            return {"document_type": "Blood Test", "confidence": 0.80, "method": "rule_fallback"}

        return {
            "document_type": "Other",
            "confidence": 0.70,
            "method": "rule_fallback"
        }
