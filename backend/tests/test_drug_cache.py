import pytest
import time
from app.services.drug_cache.drug_cache_service import DrugCacheService
from app.services.drug_cache.cache_metrics import drug_cache_metrics

@pytest.fixture(autouse=True)
def clean_cache():
    drug_cache_metrics.reset()
    yield
    drug_cache_metrics.reset()

def test_lookup_cache_hit_miss():
    cache = DrugCacheService()
    cache.clear()
    
    # Check miss
    val = cache.get_lookup("aspirin")
    assert val is None
    stats = cache.get_stats()
    assert stats["lookup_misses"] == 1
    assert stats["lookup_hits"] == 0

    # Populate and check hit
    cache.set_lookup("aspirin", {"exists": True, "matched_drug": {"drug_name": "Aspirin"}})
    val = cache.get_lookup("aspirin")
    assert val is not None
    assert val["exists"] is True
    stats = cache.get_stats()
    assert stats["lookup_hits"] == 1
    assert stats["lookup_misses"] == 1
    assert stats["lookup_hit_ratio"] == 0.5

def test_lookup_cache_expiration():
    cache = DrugCacheService()
    cache.clear()
    cache.LOOKUP_TTL = 0.01  # set TTL to 10ms
    
    cache.set_lookup("aspirin", {"exists": True})
    time.sleep(0.02)
    val = cache.get_lookup("aspirin")
    assert val is None  # expired

def test_interaction_cache_by_patient():
    cache = DrugCacheService()
    cache.clear()
    
    meds = ["Aspirin", "Warfarin"]
    res = {"severity": "HIGH", "detected_interactions": []}
    
    # Set and query
    cache.set_interaction(meds, res, patient_id="pat-99")
    val = cache.get_interaction(meds, patient_id="pat-99")
    assert val == res
    
    # Invalidate patient cache
    cache.invalidate_patient("pat-99")
    val = cache.get_interaction(meds)
    assert val is None  # should be invalidated

def test_explanation_cache_by_patient():
    cache = DrugCacheService()
    cache.clear()
    
    inters = [{"drug_a_normalized": "ASPIRIN", "drug_b_normalized": "WARFARIN", "severity": "HIGH", "description": "bleeding danger"}]
    explanation = {"patient_explanation": "Avoid combining.", "fallback_used": False}
    
    # Set and query
    cache.set_explanation(inters, explanation, patient_id="pat-99")
    val = cache.get_explanation(inters, patient_id="pat-99")
    assert val == explanation
    
    # Invalidate patient cache
    cache.invalidate_patient("pat-99")
    val = cache.get_explanation(inters)
    assert val is None  # should be invalidated
