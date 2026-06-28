import pytest
from app.services.drug_safety.recommendation_builder import RecommendationBuilder

def test_recommendation_builder():
    high_recs = RecommendationBuilder.build("HIGH")
    assert "Avoid combination." in high_recs
    assert "Immediate physician review recommended." in high_recs

    medium_recs = RecommendationBuilder.build("MEDIUM")
    assert "Use with caution." in medium_recs
    assert "Consult physician." in medium_recs

    low_recs = RecommendationBuilder.build("LOW")
    assert "Monitor patient." in low_recs

    none_recs = RecommendationBuilder.build("NONE")
    assert "No known interactions detected." in none_recs

    unknown_recs = RecommendationBuilder.build("UNKNOWN")
    assert "Interaction details are unknown." in unknown_recs

def test_recommendation_builder_case_insensitive():
    high_recs = RecommendationBuilder.build("high")
    assert "Avoid combination." in high_recs
