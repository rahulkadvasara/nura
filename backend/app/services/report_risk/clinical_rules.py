"""
Nura - Clinical Diagnostic Rules
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger("nura.report_risk.clinical_rules")


class BaseRule:
    """Base interface for all clinical rules"""
    
    def evaluate(self, labs: List[Dict[str, Any]], medications: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Evaluates rules against structured lab values and medications.
        
        Returns a list of finding dicts:
        - rule_name: str
        - severity: NORMAL, LOW, MEDIUM, HIGH, CRITICAL
        - message: str
        - flag: str
        """
        raise NotImplementedError


class DiabetesRule(BaseRule):
    def evaluate(self, labs: List[Dict[str, Any]], medications: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        findings = []
        hba1c_val = None
        glucose_val = None

        for lab in labs:
            name = lab.get("test_name", "").lower()
            val = lab.get("value")
            try:
                numeric = float(str(val))
            except (ValueError, TypeError):
                continue
                
            if "hba1c" in name or "glycated" in name:
                hba1c_val = numeric
            elif "glucose" in name or "blood sugar" in name:
                glucose_val = numeric

        if hba1c_val is not None:
            if hba1c_val >= 6.5:
                findings.append({
                    "rule_name": "Diabetes Indicator (HbA1c)",
                    "severity": "HIGH" if hba1c_val < 8.0 else "CRITICAL",
                    "message": f"Elevated HbA1c level of {hba1c_val}% indicates potential diabetes mellitus.",
                    "flag": "DIABETES_MARKER"
                })
            elif hba1c_val >= 5.7:
                findings.append({
                    "rule_name": "Prediabetes Indicator (HbA1c)",
                    "severity": "MEDIUM",
                    "message": f"HbA1c of {hba1c_val}% indicates prediabetes glycemic ranges.",
                    "flag": "DIABETES_MARKER"
                })

        if glucose_val is not None and glucose_val >= 126.0:
            findings.append({
                "rule_name": "Hyperglycemia Indicator",
                "severity": "MEDIUM" if glucose_val < 200.0 else "HIGH",
                "message": f"High fasting blood glucose level of {glucose_val} mg/dL observed.",
                "flag": "DIABETES_MARKER"
            })
            
        return findings


class KidneyRule(BaseRule):
    def evaluate(self, labs: List[Dict[str, Any]], medications: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        findings = []
        egfr_val = None
        creatinine_val = None

        for lab in labs:
            name = lab.get("test_name", "").lower()
            val = lab.get("value")
            try:
                numeric = float(str(val))
            except (ValueError, TypeError):
                continue
                
            if "egfr" in name or "glomerular filtration" in name:
                egfr_val = numeric
            elif "creatinine" in name:
                creatinine_val = numeric

        if egfr_val is not None and egfr_val < 60.0:
            severity = "MEDIUM" if egfr_val >= 30.0 else "HIGH" if egfr_val >= 15.0 else "CRITICAL"
            findings.append({
                "rule_name": "Impaired Kidney Function (eGFR)",
                "severity": severity,
                "message": f"Reduced eGFR rate of {egfr_val} mL/min/1.73m² indicates impaired glomerular filtration.",
                "flag": "KIDNEY_RISK"
            })

        if creatinine_val is not None and creatinine_val > 1.2:
            severity = "LOW" if creatinine_val < 1.8 else "MEDIUM" if creatinine_val < 3.0 else "CRITICAL"
            findings.append({
                "rule_name": "Elevated Serum Creatinine",
                "severity": severity,
                "message": f"Creatinine level of {creatinine_val} mg/dL is higher than clinical reference limits.",
                "flag": "KIDNEY_RISK"
            })
            
        return findings


class LiverRule(BaseRule):
    def evaluate(self, labs: List[Dict[str, Any]], medications: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        findings = []
        alt_val = None
        ast_val = None
        bilirubin_val = None

        for lab in labs:
            name = lab.get("test_name", "").lower()
            val = lab.get("value")
            try:
                numeric = float(str(val))
            except (ValueError, TypeError):
                continue
                
            if "alt" in name or "alanine aminotransferase" in name or "sgpt" in name:
                alt_val = numeric
            elif "ast" in name or "aspartate aminotransferase" in name or "sgot" in name:
                ast_val = numeric
            elif "bilirubin" in name:
                bilirubin_val = numeric

        if (alt_val and alt_val > 50.0) or (ast_val and ast_val > 50.0):
            val_str = f"ALT: {alt_val} U/L" if alt_val else ""
            val_str += f" | AST: {ast_val} U/L" if ast_val else ""
            findings.append({
                "rule_name": "Elevated Liver Enzymes",
                "severity": "MEDIUM",
                "message": f"Elevated hepatic transaminases ({val_str}) indicate potential liver irritation or injury.",
                "flag": "LIVER_ABNORMALITY"
            })

        if bilirubin_val is not None and bilirubin_val > 1.2:
            findings.append({
                "rule_name": "Hyperbilirubinemia Indicator",
                "severity": "MEDIUM" if bilirubin_val < 3.0 else "HIGH",
                "message": f"Elevated serum bilirubin of {bilirubin_val} mg/dL indicates potential biliary dysfunction or jaundice.",
                "flag": "LIVER_ABNORMALITY"
            })
            
        return findings


class ThyroidRule(BaseRule):
    def evaluate(self, labs: List[Dict[str, Any]], medications: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        findings = []
        tsh_val = None

        for lab in labs:
            name = lab.get("test_name", "").lower()
            val = lab.get("value")
            try:
                numeric = float(str(val))
            except (ValueError, TypeError):
                continue
                
            if "tsh" in name or "thyroid stimulating hormone" in name:
                tsh_val = numeric

        if tsh_val is not None:
            if tsh_val > 4.5:
                findings.append({
                    "rule_name": "Hypothyroidism Indicator",
                    "severity": "LOW" if tsh_val < 10.0 else "MEDIUM",
                    "message": f"Elevated TSH level of {tsh_val} uIU/mL indicates underactive thyroid gland regulation.",
                    "flag": "THYROID_ABNORMALITY"
                })
            elif tsh_val < 0.4:
                findings.append({
                    "rule_name": "Hyperthyroidism Indicator",
                    "severity": "MEDIUM",
                    "message": f"Suppressed TSH level of {tsh_val} uIU/mL indicates potential hyperthyroidism.",
                    "flag": "THYROID_ABNORMALITY"
                })
                
        return findings


class LipidRule(BaseRule):
    def evaluate(self, labs: List[Dict[str, Any]], medications: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        findings = []
        chol_val = None
        ldl_val = None

        for lab in labs:
            name = lab.get("test_name", "").lower()
            val = lab.get("value")
            try:
                numeric = float(str(val))
            except (ValueError, TypeError):
                continue
                
            if "cholesterol" in name and "total" in name:
                chol_val = numeric
            elif "ldl" in name:
                ldl_val = numeric

        if chol_val is not None and chol_val > 200.0:
            findings.append({
                "rule_name": "Hypercholesterolemia Indicator",
                "severity": "LOW" if chol_val < 240.0 else "MEDIUM",
                "message": f"Elevated total cholesterol level of {chol_val} mg/dL.",
                "flag": "LIPID_ABNORMALITY"
            })

        if ldl_val is not None and ldl_val > 130.0:
            findings.append({
                "rule_name": "Elevated LDL Cholesterol",
                "severity": "LOW" if ldl_val < 160.0 else "MEDIUM" if ldl_val < 190.0 else "HIGH",
                "message": f"LDL cholesterol of {ldl_val} mg/dL is higher than clinical thresholds.",
                "flag": "LIPID_ABNORMALITY"
            })
            
        return findings


class AnemiaRule(BaseRule):
    def evaluate(self, labs: List[Dict[str, Any]], medications: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        findings = []
        hb_val = None

        for lab in labs:
            name = lab.get("test_name", "").lower()
            val = lab.get("value")
            try:
                numeric = float(str(val))
            except (ValueError, TypeError):
                continue
                
            if "hemoglobin" in name or "hb" in name:
                hb_val = numeric

        if hb_val is not None and hb_val < 12.0:
            severity = "LOW" if hb_val >= 10.0 else "MEDIUM" if hb_val >= 8.0 else "CRITICAL"
            findings.append({
                "rule_name": "Anemia Indicator",
                "severity": severity,
                "message": f"Low hemoglobin level of {hb_val} g/dL indicates potential anemia state.",
                "flag": "ANEMIA_DETECTION"
            })
            
        return findings


class InfectionRule(BaseRule):
    def evaluate(self, labs: List[Dict[str, Any]], medications: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        findings = []
        wbc_val = None

        for lab in labs:
            name = lab.get("test_name", "").lower()
            val = lab.get("value")
            try:
                numeric = float(str(val))
            except (ValueError, TypeError):
                continue
                
            if "wbc" in name or "white blood cell" in name or "leukocyte" in name:
                wbc_val = numeric

        if wbc_val is not None:
            if wbc_val > 11.0:
                severity = "LOW" if wbc_val < 15.0 else "MEDIUM" if wbc_val < 30.0 else "CRITICAL"
                findings.append({
                    "rule_name": "Infection or Inflammatory Response (WBC)",
                    "severity": severity,
                    "message": f"Elevated white blood cells count of {wbc_val} k/uL indicates potential infection or acute inflammatory state.",
                    "flag": "INFECTION_FLAG"
                })
            elif wbc_val < 4.0:
                severity = "MEDIUM" if wbc_val >= 2.0 else "CRITICAL"
                findings.append({
                    "rule_name": "Leukopenia Indicator",
                    "severity": severity,
                    "message": f"Depressed white blood cells count of {wbc_val} k/uL indicating neutropenia risk.",
                    "flag": "INFECTION_FLAG"
                })
                
        return findings


class ClinicalRules:
    """Master evaluator holding distinct rules classes list"""

    def __init__(self):
        self.rules: List[BaseRule] = [
            DiabetesRule(),
            KidneyRule(),
            LiverRule(),
            ThyroidRule(),
            LipidRule(),
            AnemiaRule(),
            InfectionRule()
        ]

    def evaluate_all(self, labs: List[Dict[str, Any]], medications: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        findings = []
        for rule in self.rules:
            findings.extend(rule.evaluate(labs, medications))
        return findings
