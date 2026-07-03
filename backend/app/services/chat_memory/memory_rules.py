"""
Nura - Memory Rules Engine
Deterministic keyword and rules parsing for conversation memory worthiness
"""

import re
from typing import Dict, Any, List

CLINICAL_PATTERNS = {
    "symptoms": r"\b(pain|cough|fever|ache|dizzy|nausea|vomit|rash|swelling|shortness|fatigue|bleeding|symptom)\b",
    "medications": r"\b(pill|drug|tablet|medication|dose|mg|prescription|side\s+effect|refill|capsule|antibiotic|dosage)\b",
    "allergies": r"\b(allergy|allergic|reaction|hives|anaphylaxis|swelling)\b",
    "diagnoses": r"\b(diagnose|diagnosis|disease|chronic|diabetic|hypertension|syndrome|cancer|asthma|arthritis)\b",
    "lifestyle": r"\b(exercise|diet|smoke|alcohol|sleep|quit|workout|weight|calories|nutrition)\b",
    "followup": r"\b(follow\s*up|schedule|appointment|visit|recheck|referral|revisit)\b",
    "preferences": r"\b(prefer|like|dislike|avoid|want|choose|choice)\b"
}

CASUAL_PATTERNS = r"\b(hello|hi|hey|greetings|thanks|thank\s+you|bye|goodbye|welcome|sorry|test|retry)\b"


def evaluate_conversation_deterministically(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Evaluates semantic value, clinical relevance, personal preferences, follow-up importance,
    novelty, and conversation quality based on deterministic regex and length rules.
    """
    combined_text = " ".join([m.get("content", "").lower() for m in messages])
    
    # 1. Length & Small Talk Check
    # If the total conversation is very short or matches casual small talk, rank low
    is_casual = len(re.findall(CASUAL_PATTERNS, combined_text)) > 0
    total_len = len(combined_text)
    
    if total_len < 40 or (is_casual and total_len < 100):
        return {
            "semantic_score": 0.1,
            "clinical_score": 0.1,
            "preference_score": 0.1,
            "followup_score": 0.1,
            "novelty_score": 0.1,
            "quality_score": 0.1,
            "memory_score": 0.1,
            "should_store_chat_memory": False,
            "should_update_patient_memory": False
        }

    # 2. Count Matches
    symptom_matches = len(re.findall(CLINICAL_PATTERNS["symptoms"], combined_text))
    med_matches = len(re.findall(CLINICAL_PATTERNS["medications"], combined_text))
    allergy_matches = len(re.findall(CLINICAL_PATTERNS["allergies"], combined_text))
    diag_matches = len(re.findall(CLINICAL_PATTERNS["diagnoses"], combined_text))
    lifestyle_matches = len(re.findall(CLINICAL_PATTERNS["lifestyle"], combined_text))
    followup_matches = len(re.findall(CLINICAL_PATTERNS["followup"], combined_text))
    pref_matches = len(re.findall(CLINICAL_PATTERNS["preferences"], combined_text))

    # 3. Calculate Scores (normalized between 0.0 and 1.0)
    clinical_indicators = symptom_matches + med_matches + allergy_matches + diag_matches + lifestyle_matches + followup_matches
    
    # Clinical Score
    clinical_score = min(1.0, clinical_indicators * 0.25)
    if clinical_indicators == 0:
        clinical_score = 0.0
        
    # Preference Score
    preference_score = min(1.0, pref_matches * 0.5)
    
    # Followup Score
    followup_score = min(1.0, followup_matches * 0.5)
    
    # Novelty Score (based on symptoms/diagnoses discussions)
    novelty_indicators = symptom_matches + diag_matches + allergy_matches
    novelty_score = min(1.0, novelty_indicators * 0.33)
    
    # Quality Score (based on length and detailed response)
    quality_score = min(1.0, total_len / 1000.0)
    if total_len > 150:
        quality_score = max(0.5, quality_score)
        
    # Semantic Score (detailed content, preferences, clinical)
    semantic_score = min(1.0, (total_len / 600.0) + (clinical_indicators * 0.1) + (pref_matches * 0.2))
    if is_casual:
        semantic_score = max(0.1, semantic_score - 0.3)

    # General Memory Score
    memory_score = (semantic_score + clinical_score + quality_score) / 3.0

    # Rules Decider
    should_store_chat_memory = semantic_score >= 0.5
    should_update_patient_memory = clinical_score >= 0.6

    return {
        "semantic_score": round(semantic_score, 2),
        "clinical_score": round(clinical_score, 2),
        "preference_score": round(preference_score, 2),
        "followup_score": round(followup_score, 2),
        "novelty_score": round(novelty_score, 2),
        "quality_score": round(quality_score, 2),
        "memory_score": round(memory_score, 2),
        "should_store_chat_memory": should_store_chat_memory,
        "should_update_patient_memory": should_update_patient_memory
    }
