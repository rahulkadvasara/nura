"""
Nura Backend - Intent Classifier Unit Tests
Verifies deterministic keyword and regex weighted classifications and confidence scoring formulas.
"""

import pytest
from app.agents.router.intent_classifier import IntentClassifier


def test_classifier_empty_query():
    """Verify empty queries return UNKNOWN intent with 0.0 confidence"""
    classifier = IntentClassifier()
    result = classifier.classify("")
    assert result.intent == "UNKNOWN"
    assert result.confidence == 0.0
    assert "empty_query" in result.matched_rules


def test_classifier_greetings():
    """Verify greeting keywords route to GREETING"""
    classifier = IntentClassifier()
    result = classifier.classify("Hello there! Good morning.")
    assert result.intent == "GREETING"
    assert result.confidence > 0.0
    assert any("keyword:hello" in r or "regex:" in r for r in result.matched_rules)


def test_classifier_medical_question():
    """Verify medical question keywords and patterns route to MEDICAL_QUESTION"""
    classifier = IntentClassifier()
    result = classifier.classify("What is the cause of chronic diabetes?")
    assert result.intent == "MEDICAL_QUESTION"
    assert result.confidence >= 0.5


def test_classifier_symptom_analysis():
    """Verify symptoms list routes to SYMPTOM_ANALYSIS"""
    classifier = IntentClassifier()
    result = classifier.classify("I have a severe headache and high fever with runny nose")
    assert result.intent == "SYMPTOM_ANALYSIS"
    assert result.confidence >= 0.5


def test_classifier_drug_interaction():
    """Verify drug interaction patterns route to DRUG_INTERACTION"""
    classifier = IntentClassifier()
    result = classifier.classify("Is it safe to take paracetamol together with ibuprofen?")
    assert result.intent == "DRUG_INTERACTION"
    assert result.confidence >= 0.5


def test_classifier_doctor_recommendation():
    """Verify doctor suggestions route to DOCTOR_RECOMMENDATION"""
    classifier = IntentClassifier()
    result = classifier.classify("Can you suggest a good dermatologist cardiologist specialist?")
    assert result.intent == "DOCTOR_RECOMMENDATION"
    assert result.confidence >= 0.5


def test_classifier_unknown_query():
    """Verify gibberish routes to UNKNOWN with 0.0 confidence"""
    classifier = IntentClassifier()
    result = classifier.classify("xyzabc qwer")
    assert result.intent == "UNKNOWN"
    assert result.confidence == 0.0
    assert "fallback:no_rules_matched" in result.matched_rules
