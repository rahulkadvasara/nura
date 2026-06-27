"""
Nura Backend - Intent Registry Unit Tests
Verifies default mappings, dynamic registrations, and duplicate name protection checks.
"""

import pytest
from app.agents.router.intent_registry import IntentRegistry


def test_registry_default_mappings():
    """Verify registry loads default intent-to-agent maps correctly"""
    registry = IntentRegistry()
    mappings = registry.list_mappings()
    
    assert mappings["MEDICAL_QUESTION"] == "MedicalKnowledgeAgent"
    assert mappings["GREETING"] == "GreetingAgent"
    assert mappings["SYMPTOM_ANALYSIS"] == "SymptomAgent"
    assert mappings["UNKNOWN"] == "UnknownAgent"


def test_registry_dynamic_registration():
    """Verify dynamic mapping additions register successfully"""
    registry = IntentRegistry()
    registry.register_intent("NEW_TEST_INTENT", "TestSpecialistAgent")
    
    assert registry.get_agent("NEW_TEST_INTENT") == "TestSpecialistAgent"
    assert registry.get_agent("new_test_intent") == "TestSpecialistAgent"


def test_registry_duplicate_registration_protection():
    """Verify dynamic registration throws ValueError on duplicate registrations"""
    registry = IntentRegistry()
    
    # Try registering already mapped MEDICAL_QUESTION
    with pytest.raises(ValueError) as exc:
        registry.register_intent("MEDICAL_QUESTION", "AnotherMedicalAgent")
    assert "Duplicate mapping error" in str(exc.value)

    # Register new one first
    registry.register_intent("INVOICE_BILLING", "BillingAgent")
    
    # Registering duplicate should fail
    with pytest.raises(ValueError) as exc:
        registry.register_intent("INVOICE_BILLING", "NewBillingAgent")
    assert "Duplicate mapping error" in str(exc.value)


def test_registry_clear():
    """Verify registry resets mappings back to default configurations"""
    registry = IntentRegistry()
    registry.register_intent("BILLING", "BillingAgent")
    assert registry.get_agent("BILLING") == "BillingAgent"
    
    registry.clear()
    assert registry.get_agent("BILLING") is None
    assert registry.get_agent("MEDICAL_QUESTION") == "MedicalKnowledgeAgent"
