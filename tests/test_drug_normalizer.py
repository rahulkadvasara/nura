import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

import pytest
from app.services.drug_safety.normalizer import DrugNormalizer

def test_drug_normalizer_basic():
    # Casing and spaces
    assert DrugNormalizer.normalize("Paracetamol") == "paracetamol"
    assert DrugNormalizer.normalize("  IBUPROFEN  ") == "ibuprofen"
    assert DrugNormalizer.normalize("Metformin    HCL") == "metformin hcl"

def test_drug_normalizer_dosage_strengths():
    # Strengths with mg, mcg, g, ml, %, iu, units, u
    assert DrugNormalizer.normalize("Paracetamol 650mg") == "paracetamol"
    assert DrugNormalizer.normalize("Ibuprofen 400 mg") == "ibuprofen"
    assert DrugNormalizer.normalize("Fentanyl 50mcg") == "fentanyl"
    assert DrugNormalizer.normalize("Fentanyl 50 mcg") == "fentanyl"
    assert DrugNormalizer.normalize("Amoxicillin 1g") == "amoxicillin"
    assert DrugNormalizer.normalize("Amoxicillin 1 g") == "amoxicillin"
    assert DrugNormalizer.normalize("Prednisolone 0.5% drops") == "prednisolone drops"
    assert DrugNormalizer.normalize("Insulin 100u") == "insulin"
    assert DrugNormalizer.normalize("Insulin 100 u") == "insulin"
    assert DrugNormalizer.normalize("Vitamin D 1000iu") == "vitamin d"

def test_drug_normalizer_dosage_forms():
    # Common suffix forms
    assert DrugNormalizer.normalize("Ibuprofen Tablet") == "ibuprofen"
    assert DrugNormalizer.normalize("Amoxicillin Capsules") == "amoxicillin"
    assert DrugNormalizer.normalize("Paracetamol Tablets") == "paracetamol"
    assert DrugNormalizer.normalize("Lidocaine Gel") == "lidocaine"
    assert DrugNormalizer.normalize("Erythromycin Ointment") == "erythromycin"

def test_drug_normalizer_standalone_numbers():
    # Standalone numbers (often strengths without units)
    assert DrugNormalizer.normalize("Metformin 500") == "metformin"
    assert DrugNormalizer.normalize("Atorvastatin 10") == "atorvastatin"

def test_drug_normalizer_mixed():
    # Mixed dosage and forms
    assert DrugNormalizer.normalize("Paracetamol 650mg Tablet") == "paracetamol"
    assert DrugNormalizer.normalize("Amoxicillin 500 mg Capsules") == "amoxicillin"

def test_drug_normalizer_edge_cases():
    # Names with embedded numbers or symbols
    assert DrugNormalizer.normalize("Vitamin D3") == "vitamin d3"
    assert DrugNormalizer.normalize("Co-Q10") == "co-q10"
    assert DrugNormalizer.normalize("") == ""
    assert DrugNormalizer.normalize(None) == ""
