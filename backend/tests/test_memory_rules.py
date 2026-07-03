"""
Nura - Memory Rules Engine Tests
Verifies worthiness scoring, clinical weights, and small talk filtering
"""

import pytest
from app.services.chat_memory.memory_rules import evaluate_conversation_deterministically


def test_casual_small_talk_low_scores():
    # Casual small talk greetings
    messages = [
        {"role": "user", "content": "Hello how are you doing?"},
        {"role": "assistant", "content": "I am fine thank you, how can I help you today?"}
    ]
    res = evaluate_conversation_deterministically(messages)
    assert res["should_store_chat_memory"] is False
    assert res["should_update_patient_memory"] is False
    assert res["memory_score"] <= 0.2


def test_clinical_conversation_high_scores():
    # Dialogue containing medical symptoms, medication names, and advice
    messages = [
        {"role": "user", "content": "My head hurts and I have a bad fever. I took Aspirin 500mg but it did not help."},
        {"role": "assistant", "content": "I advise scheduling a recheck visit. Watch for worsening symptoms or allergies."}
    ]
    res = evaluate_conversation_deterministically(messages)
    # Check that clinical indicators are scored highly
    assert res["clinical_score"] >= 0.5
    assert res["semantic_score"] >= 0.5
    assert res["should_store_chat_memory"] is True
