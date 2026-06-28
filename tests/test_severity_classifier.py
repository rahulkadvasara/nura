import pytest
from app.services.drug_safety.severity_classifier import SeverityClassifier

def test_severity_classifier_empty():
    assert SeverityClassifier.classify([]) == "NONE"
    assert SeverityClassifier.classify(None) == "NONE"

def test_severity_classifier_single():
    assert SeverityClassifier.classify(["LOW"]) == "LOW"
    assert SeverityClassifier.classify(["HIGH"]) == "HIGH"
    assert SeverityClassifier.classify(["unknown"]) == "UNKNOWN"

def test_severity_classifier_precedence():
    # HIGH takes highest precedence
    assert SeverityClassifier.classify(["LOW", "HIGH", "MEDIUM"]) == "HIGH"
    assert SeverityClassifier.classify(["LOW", "MEDIUM"]) == "MEDIUM"
    assert SeverityClassifier.classify(["LOW", "UNKNOWN"]) == "LOW"
    assert SeverityClassifier.classify(["UNKNOWN", "NONE"]) == "UNKNOWN"

def test_severity_classifier_invalid_values():
    assert SeverityClassifier.classify(["invalid_val"]) == "UNKNOWN"
    assert SeverityClassifier.classify([None, "LOW"]) == "LOW"
