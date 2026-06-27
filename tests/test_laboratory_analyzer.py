import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

import pytest
from app.services.report_risk.laboratory_analyzer import LaboratoryAnalyzer


def test_parse_reference_range():
    analyzer = LaboratoryAnalyzer()
    
    # 1. Range format
    min_val, max_val = analyzer.parse_reference_range("13.0 - 17.5")
    assert min_val == 13.0
    assert max_val == 17.5

    # 2. Max format
    min_val, max_val = analyzer.parse_reference_range("< 200")
    assert min_val == 0.0
    assert max_val == 200.0

    # 3. Min format
    min_val, max_val = analyzer.parse_reference_range(">= 50")
    assert min_val == 50.0
    assert max_val is None

    # 4. None / malformed format
    min_val, max_val = analyzer.parse_reference_range(None)
    assert min_val is None
    assert max_val is None


def test_evaluate_result_normal():
    analyzer = LaboratoryAnalyzer()
    res = analyzer.evaluate_result("Hemoglobin", 14.5, "g/dL", "13.0 - 17.0")
    
    assert res["status"] == "NORMAL"
    assert not res["is_abnormal"]
    assert not res["is_critical"]


def test_evaluate_result_abnormal():
    analyzer = LaboratoryAnalyzer()
    
    # Low alert
    res_low = analyzer.evaluate_result("Hemoglobin", 11.0, "g/dL", "13.0 - 17.0")
    assert res_low["status"] == "LOW"
    assert res_low["is_abnormal"]
    assert not res_low["is_critical"]

    # High alert
    res_high = analyzer.evaluate_result("Glucose", 140, "mg/dL", "70 - 100")
    assert res_high["status"] == "HIGH"
    assert res_high["is_abnormal"]
    assert not res_high["is_critical"]


def test_evaluate_result_critical():
    analyzer = LaboratoryAnalyzer()
    
    # Critical low
    res_crit_low = analyzer.evaluate_result("Hemoglobin", 6.5, "g/dL", "13.0 - 17.0")
    assert res_crit_low["status"] == "CRITICAL_LOW"
    assert res_crit_low["is_abnormal"]
    assert res_crit_low["is_critical"]

    # Critical high
    res_crit_high = analyzer.evaluate_result("Glucose", 350, "mg/dL", "70 - 100")
    assert res_crit_high["status"] == "CRITICAL_HIGH"
    assert res_crit_high["is_abnormal"]
    assert res_crit_high["is_critical"]


def test_evaluate_result_fallback_ranges():
    analyzer = LaboratoryAnalyzer()
    # Missing range_str, should fall back to HbA1c defaults
    res = analyzer.evaluate_result("HbA1c", 7.2, "%", None)
    
    assert res["status"] == "HIGH"
    assert res["ref_min"] == 4.0
    assert res["ref_max"] == 5.6
