"""
Nura - Intent Detection Service
Deterministic classifier for identifying retrieval intent categories based on keyword and regex rules.
"""
import re
from typing import Dict, Tuple

class IntentDetectionService:
    """Deterministic keyword and regex-based classifier for AI retrieval intents"""

    # Keyword lists for intent scoring
    INTENT_KEYWORDS: Dict[str, list] = {
        "medical_question": [
            "what is", "how to", "symptom", "disease", "illness", "treatment", "cause", "prevent",
            "vaccine", "medicine", "diagnose", "therapy", "clinical", "virus", "infection",
            "chronic", "pain", "fever", "cough", "allergy"
        ],
        "report_analysis": [
            "report", "lab", "test result", "blood test", "scan", "mri", "x-ray", "xray", "pdf",
            "findings", "cbc", "panel", "pathology", "ultrasound", "biopsy", "cholesterol", "glucose"
        ],
        "drug_question": [
            "drug", "medication", "pill", "side effect", "dosage", "interaction", "contraindication",
            "tablet", "capsule", "prescribe", "rx", "ibuprofen", "aspirin", "paracetamol", "antibiotic"
        ],
        "doctor_recommendation": [
            "recommend", "find doctor", "doctor profile", "specialist", "cardiologist", "pediatrician",
            "dermatologist", "appointment with", "consult doctor", "physician", "surgeon", "clinic"
        ],
        "conversation_recall": [
            "remember", "last discussion", "previous chat", "you said", "we talked", "history",
            "recall", "previous conversation", "our chat", "earlier", "told you"
        ],
        "general_health": [
            "diet", "exercise", "fitness", "wellness", "lifestyle", "weight loss", "nutrition",
            "sleep", "hydration", "calories", "workout", "healthy", "routine"
        ]
    }

    # Regular expressions for specific patterns
    INTENT_REGEX: Dict[str, list] = {
        "medical_question": [
            r"\b(what|how|why)\b.*\b(symptom|cause|treatment|cure)\b",
            r"\bis\b.*\b(contagious|genetic|treatable)\b"
        ],
        "report_analysis": [
            r"\b(analyze|check|read|review)\b.*\b(report|test|results|labs)\b",
            r"\b(what do my|explain my)\b.*\b(results|labs|numbers)\b"
        ],
        "drug_question": [
            r"\b(can i take|safe to take)\b",
            r"\b(side effect|interaction|dose|dosage)\b.*\b(of|for)\b"
        ],
        "doctor_recommendation": [
            r"\b(suggest|find|need|recommend)\b.*\b(doctor|specialist|physician|therapist)\b",
            r"\b(who is the best)\b.*\b(for|in)\b"
        ],
        "conversation_recall": [
            "what did (we|i|you) say",
            "do you remember",
            "as we discussed"
        ],
        "general_health": [
            r"\b(how to (lose weight|stay healthy|eat well))\b",
            r"\b(diet plan|exercise routine)\b"
        ]
    }

    def detect_intent(self, query: str) -> str:
        """Detect intent from query string and return winning intent string"""
        intent, _ = self.detect_intent_with_scores(query)
        return intent

    def detect_intent_with_scores(self, query: str) -> Tuple[str, Dict[str, int]]:
        """
        Analyze query and return winning intent along with raw match scores dictionary.
        Enables debugging of deterministic scoring logic.
        """
        if not query or not query.strip():
            return "unknown", {k: 0 for k in self.INTENT_KEYWORDS.keys()}

        # 0. Check Cache
        from app.services.rag_cache_service import get_rag_cache_service
        cache_svc = get_rag_cache_service()
        cached = cache_svc.get_query(query)
        if cached is not None:
            return cached[0], cached[1]

        cleaned_query = query.lower().strip()
        scores = {k: 0 for k in self.INTENT_KEYWORDS.keys()}

        # 1. Score based on keyword counts
        for intent, keywords in self.INTENT_KEYWORDS.items():
            for kw in keywords:
                # Count matches using string find
                count = cleaned_query.count(kw)
                if count > 0:
                    scores[intent] += count * 2 # Weight keywords highly

        # 2. Score based on regex matches
        for intent, patterns in self.INTENT_REGEX.items():
            for pattern in patterns:
                try:
                    matches = re.findall(pattern, cleaned_query)
                    if matches:
                        scores[intent] += len(matches) * 5 # Weight direct patterns heavily
                except Exception:
                    pass

        # 3. Determine winner
        max_score = 0
        winner = "unknown"
        for intent, score in scores.items():
            if score > max_score:
                max_score = score
                winner = intent

        # If no score matches, default to unknown
        if max_score == 0:
            winner = "unknown"

        cache_svc.set_query(query, winner, scores)
        return winner, scores

def get_intent_detection_service() -> IntentDetectionService:
    """Dependency injection provider for IntentDetectionService"""
    return IntentDetectionService()
