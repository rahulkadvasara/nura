"""
Nura - Intent Classifier
Deterministic keyword and regex weighted scoring query intent classifier.
"""

import re
from typing import Dict, List, Tuple
from app.core.ai_config import ai_settings
from app.agents.router.schemas import IntentClassificationResult


class IntentClassifier:
    """Fast, deterministic keyword matching and regular expressions query classifier"""

    # Keyword lists for the 10 core classification categories
    INTENT_KEYWORDS: Dict[str, List[str]] = {
        "GREETING": [
            "hello", "hi", "hey", "greetings", "hola", "yo", "good morning", 
            "good afternoon", "good evening", "howdy", "sup"
        ],
        "GENERAL_CHAT": [
            "how are you", "who are you", "what can you do", "talk to me", "tell me a joke", 
            "chatter", "name", "nura", "developer", "creator", "help me chat", "what is your age"
        ],
        "MEDICAL_QUESTION": [
            "explain", "cause", "treat", "treatment", "cure", "vaccine", "prevention", 
            "chronic", "infection", "clinical", "research", "disease", "virus", "bacteria", 
            "symptom", "illness", "diagnose", "clinical research", "contagious", "therapy"
        ],
        "SYMPTOM_ANALYSIS": [
            "headache", "pain", "cough", "fever", "nausea", "fatigue", "vomit", "sore throat", 
            "feeling sick", "chest pain", "backache", "stomach ache", "dizzy", "rash", "cramps",
            "shivering", "congested", "runny nose", "sneezing", "wheezing"
        ],
        "REPORT_ANALYSIS": [
            "report", "lab", "blood test", "pdf", "cholesterol level", "blood sugar", 
            "check results", "explain results", "findings", "cbc", "mri", "scan", "x-ray",
            "xray", "pathology", "ultrasound", "biopsy", "glucose levels", "lipid profile"
        ],
        "DRUG_INTERACTION": [
            "drug", "interaction", "paracetamol", "ibuprofen", "aspirin", "side effect", 
            "pill", "tablet", "rx", "dose", "dosage", "contraindication", "take together", 
            "medication side effect", "capsule", "antibiotic", "prescription details"
        ],
        "DOCTOR_RECOMMENDATION": [
            "recommend", "find physician", "suggest specialist", "cardiologist", "dermatologist", 
            "pediatrician", "best doctor", "list doctors", "specialist clinic", "surgeon", 
            "therapist", "find oncologist", "consult doc"
        ],
        "REMINDER": [
            "remind", "pills alarm", "schedule medicine", "alert me", "notify", "daily reminder", 
            "wake up alarm", "dose time", "med alert", "remind me to take", "alarm alarm"
        ],
        "APPOINTMENT": [
            "book appointment", "schedule slot", "consultations", "schedule visit", "meet doctor", 
            "consult", "calendar", "booking", "slots availability", "make appointment", 
            "appointment slot", "meet physician"
        ],
        "CONVERSATION_RECALL": [
            "remember", "last discussion", "previous chat", "recall", "history", "earlier", 
            "what did we say", "discussed earlier", "last time we talked", "history logs",
            "do you remember", "as we discussed"
        ]
    }

    # Regex patterns for query context structure detection
    INTENT_REGEX: Dict[str, List[str]] = {
        "GREETING": [
            r"^\b(hello|hi|hey|hola|greetings)\b",
            r"\b(good\s+(morning|afternoon|evening))\b"
        ],
        "GENERAL_CHAT": [
            r"\b(how\s+are\s+you|who\s+are\s+you|what\s+is\s+your\s+name)\b",
            r"\b(what\s+can\s+you\s+do|how\s+do\s+you\s+work|who\s+made\s+you)\b"
        ],
        "MEDICAL_QUESTION": [
            r"\b(what\s+is\s+a|what\s+causes|how\s+to\s+prevent)\s+\b(symptom|disease|virus|infection|illness)\b",
            r"\b(information\s+on|tell\s+me\s+about)\s+\b(chronic|cancer|diabetes|allergy)\b"
        ],
        "SYMPTOM_ANALYSIS": [
            r"\b(i\s+have\s+a|feeling|suffering\s+from)\s+\b(headache|cough|fever|rash|pain|coughing)\b",
            r"\b(my\s+body|chest|throat|head)\s+(hurts|feels|aching)\b"
        ],
        "REPORT_ANALYSIS": [
            r"\b(analyze|check|read|review)\s+\b(report|test|results|labs|cbc|mri|xray)\b",
            r"\b(what\s+do\s+my|explain\s+my)\s+\b(results|labs|numbers|cholesterol|sugar)\b"
        ],
        "DRUG_INTERACTION": [
            r"\b(can\s+i\s+take|safe\s+to\s+take|mix)\b.*\b(together|with|and)\b",
            r"\b(side\s+effect|interaction|dosage|dose)\s+of\b.*\b(ibuprofen|aspirin|paracetamol|drug|medication)\b"
        ],
        "DOCTOR_RECOMMENDATION": [
            r"\b(recommend|find|need|suggest)\s+a\s+\b(doctor|specialist|physician|therapist|pediatrician|cardiologist)\b",
            r"\b(who\s+is\s+the\s+best)\b.*\b(specialist|doctor|surgeon)\b"
        ],
        "REMINDER": [
            r"\b(remind\s+me\s+to|set\s+reminder|alarm\s+for)\b",
            r"\b(schedule\s+med|medication\s+alert|pill\s+reminder)\b"
        ],
        "APPOINTMENT": [
            r"\b(book|schedule|reserve|make)\s+an\s+\b(appointment|consultation|visit|consult)\b",
            r"\b(meet\s+the\s+doctor|doctor\s+visit\s+slot)\b"
        ],
        "CONVERSATION_RECALL": [
            r"\b(do\s+you\s+remember|what\s+did\s+we\s+say|what\s+did\s+i\s+tell\s+you)\b",
            r"\b(previous\s+(conversation|chat|discussion)|last\s+time\s+we\s+talked)\b"
        ]
    }

    def classify(self, query: str) -> IntentClassificationResult:
        """
        Deterministic, fast weighted classification of user query text.
        Calculates match scores and confidence rating ratios.
        """
        if not query or not query.strip():
            return IntentClassificationResult(
                intent="UNKNOWN",
                confidence=0.0,
                matched_rules=["empty_query"],
                candidate_intents={"UNKNOWN": 0.0}
            )

        query_lower = query.lower().strip()
        scores: Dict[str, float] = {intent: 0.0 for intent in self.INTENT_KEYWORDS.keys()}
        matched_rules: List[str] = []

        # 1. Keywords Evaluation Matching
        if ai_settings.ROUTER_ENABLE_KEYWORDS:
            for intent, keywords in self.INTENT_KEYWORDS.items():
                for kw in keywords:
                    if len(kw) <= 3:
                        pattern = r"\b" + re.escape(kw) + r"\b"
                        count = len(re.findall(pattern, query_lower))
                    else:
                        count = query_lower.count(kw)
                    if count > 0:
                        score_increment = count * 2.0
                        scores[intent] += score_increment
                        matched_rules.append(f"keyword:{kw}")

        # 2. Regex Patterns Evaluation Matching
        if ai_settings.ROUTER_ENABLE_REGEX:
            for intent, patterns in self.INTENT_REGEX.items():
                for p_str in patterns:
                    matches = re.findall(p_str, query_lower, re.IGNORECASE)
                    count = len(matches)
                    if count > 0:
                        score_increment = count * 5.0
                        scores[intent] += score_increment
                        matched_rules.append(f"regex:{p_str}")

        # Compute winning intent and confidence ratios
        winning_intent = "UNKNOWN"
        winning_score = 0.0
        total_score = sum(scores.values())

        for intent, score in scores.items():
            if score > winning_score:
                winning_score = score
                winning_intent = intent

        # Confidence calculation metric combining distinction ratio and total score strength
        confidence = 0.0
        if winning_score > 0.0:
            distinction = winning_score / total_score
            # Diminishing strength multiplier: single keyword matches get capped confidence
            strength = winning_score / (winning_score + 3.0)
            confidence = round(distinction * strength, 2)
            # Cap maximum value at 1.0
            confidence = min(confidence, 1.0)
        else:
            # Fallback to UNKNOWN
            winning_intent = "UNKNOWN"
            scores = {"UNKNOWN": 0.0}
            matched_rules.append("fallback:no_rules_matched")

        # Exclude 0 score candidate intents
        candidate_intents = {k: v for k, v in scores.items() if v > 0.0}
        if not candidate_intents:
            candidate_intents = {"UNKNOWN": 0.0}

        return IntentClassificationResult(
            intent=winning_intent,
            confidence=confidence,
            matched_rules=matched_rules,
            candidate_intents=candidate_intents
        )
