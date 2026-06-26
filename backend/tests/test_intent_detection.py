"""
Nura - Unit tests for IntentDetectionService
"""
import pytest
from app.services.intent_detection_service import IntentDetectionService

@pytest.fixture
def intent_service():
    return IntentDetectionService()

def test_intent_detection_medical_question(intent_service):
    """Test queries with medical words result in MEDICAL_QUESTION"""
    query = "What are the common symptoms and treatment causes for heart disease?"
    intent, scores = intent_service.detect_intent_with_scores(query)
    assert intent == "medical_question"
    assert scores["medical_question"] > 0

def test_intent_detection_report_analysis(intent_service):
    """Test queries about reports result in REPORT_ANALYSIS"""
    query = "Could you please analyze my glucose lab blood test report results?"
    intent, scores = intent_service.detect_intent_with_scores(query)
    assert intent == "report_analysis"
    assert scores["report_analysis"] > 0

def test_intent_detection_drug_question(intent_service):
    """Test queries about drugs result in DRUG_QUESTION"""
    query = "Are there any tablet side effects and contraindications for aspirin pill?"
    intent, scores = intent_service.detect_intent_with_scores(query)
    assert intent == "drug_question"
    assert scores["drug_question"] > 0

def test_intent_detection_doctor_recommendation(intent_service):
    """Test queries about doctors result in DOCTOR_RECOMMENDATION"""
    query = "Can you recommend a cardiologist doctor specialist for an appointment?"
    intent, scores = intent_service.detect_intent_with_scores(query)
    assert intent == "doctor_recommendation"
    assert scores["doctor_recommendation"] > 0

def test_intent_detection_conversation_recall(intent_service):
    """Test queries asking about conversation history result in CONVERSATION_RECALL"""
    query = "Do you remember what you said in our previous discussion earlier?"
    intent, scores = intent_service.detect_intent_with_scores(query)
    assert intent == "conversation_recall"
    assert scores["conversation_recall"] > 0

def test_intent_detection_general_health(intent_service):
    """Test queries about diets and exercise result in GENERAL_HEALTH"""
    query = "Tell me about a healthy diet plan and exercise routine."
    intent, scores = intent_service.detect_intent_with_scores(query)
    assert intent == "general_health"
    assert scores["general_health"] > 0

def test_intent_detection_unknown_fallback(intent_service):
    """Test queries with no keyword match fallback to UNKNOWN"""
    query = "Hello, nice to meet you."
    intent, scores = intent_service.detect_intent_with_scores(query)
    assert intent == "unknown"
    assert all(score == 0 for score in scores.values())
