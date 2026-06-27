import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

import pytest
from app.services.report_risk.recommendation_engine import RecommendationEngine


def test_generate_recommendations_normal():
    engine = RecommendationEngine()
    recs = engine.generate_recommendations([], 0)
    assert len(recs) == 0


def test_generate_recommendations_critical():
    engine = RecommendationEngine()
    # 1 critical lab value, no rule findings
    recs = engine.generate_recommendations([], 1)
    
    assert len(recs) > 0
    assert any(r["recommendation_type"] == "Emergency attention" for r in recs)
    assert any(r["urgency"] == "IMMEDIATE" for r in recs)


def test_generate_recommendations_diabetes():
    engine = RecommendationEngine()
    findings = [{
        "rule_name": "Diabetes Indicator (HbA1c)",
        "severity": "HIGH",
        "flag": "DIABETES_MARKER",
        "message": "HbA1c is 7.2%"
    }]
    
    recs = engine.generate_recommendations(findings, 0)
    
    assert len(recs) > 0
    # Should include physician consultation, specialist referral (endocrinologist), lifestyle changes, and retest
    assert any(r["recommendation_type"] == "Consult physician" for r in recs)
    assert any(r["recommendation_type"] == "Specialist referral" for r in recs)
    assert any(r["recommendation_type"] == "Lifestyle modification" for r in recs)
    assert any(r["recommendation_type"] == "Repeat laboratory test" for r in recs)
    
    # Check that disclaimer is attached
    assert all("disclaimer" in r and r["disclaimer"] for r in recs)
