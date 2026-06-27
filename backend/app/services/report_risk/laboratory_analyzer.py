"""
Nura - Laboratory Results Risk Analyzer
"""

import re
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("nura.report_risk.laboratory_analyzer")


class LaboratoryAnalyzer:
    """Analyzes laboratory parameters values against reference thresholds to flag abnormal or critical states"""

    # Clinical fallback standard reference ranges
    DEFAULT_RANGES = {
        "hemoglobin": (12.0, 17.5, "g/dL"),
        "glucose": (70.0, 100.0, "mg/dL"),
        "hba1c": (4.0, 5.6, "%"),
        "tsh": (0.4, 4.5, "uIU/mL"),
        "cholesterol": (0.0, 199.0, "mg/dL"),
        "ldl": (0.0, 99.0, "mg/dL"),
        "creatinine": (0.5, 1.2, "mg/dL"),
        "wbc": (4.0, 11.0, "k/uL"),
        "potassium": (3.5, 5.1, "mEq/L")
    }

    # Clinical critical alarm limits
    CRITICAL_LIMITS = {
        "hemoglobin": (7.0, 20.0),
        "glucose": (50.0, 300.0),
        "creatinine": (None, 3.0),
        "wbc": (2.0, 30.0),
        "potassium": (3.0, 6.2)
    }

    def parse_reference_range(self, range_str: Optional[str]) -> Tuple[Optional[float], Optional[float]]:
        """Parses reference range string (e.g. '13.0 - 17.0', '< 200', '> 50') into (min_val, max_val)"""
        if not range_str:
            return None, None

        val = range_str.strip()
        
        # 1. Range format: "13.0 - 17.0" or "13.0-17.0"
        match = re.match(r"^([\d\.]+)\s*[\-\u2013\u2014]\s*([\d\.]+)$", val)
        if match:
            try:
                return float(match.group(1)), float(match.group(2))
            except ValueError:
                pass

        # 2. Max format: "< 200" or "<200" or "<=200"
        match = re.match(r"^<=\s*([\d\.]+)|^<\s*([\d\.]+)", val)
        if match:
            grp = match.group(1) or match.group(2)
            try:
                return 0.0, float(grp)
            except ValueError:
                pass

        # 3. Min format: "> 50" or ">= 50"
        match = re.match(r"^>=\s*([\d\.]+)|^>\s*([\d\.]+)", val)
        if match:
            grp = match.group(1) or match.group(2)
            try:
                return float(grp), None
            except ValueError:
                pass

        return None, None

    def evaluate_result(self, test_name: str, value: Any, unit: Optional[str] = None, range_str: Optional[str] = None) -> Dict[str, Any]:
        """Evaluates laboratory parameter and returns dict:
        - status: NORMAL, LOW, HIGH, CRITICAL_LOW, CRITICAL_HIGH
        - is_abnormal: bool
        - is_critical: bool
        - ref_min: float or None
        - ref_max: float or None
        """
        name_lower = test_name.strip().lower()
        
        # Parse numeric value
        numeric_val = None
        if value is not None:
            try:
                numeric_val = float(str(value))
            except ValueError:
                pass

        # If value is non-numeric, treat as NORMAL unless custom labels match
        if numeric_val is None:
            status = "NORMAL"
            val_str = str(value).strip().upper()
            if any(term in val_str for term in ("ABNORMAL", "POSITIVE", "REACTIVE", "HIGH")):
                status = "HIGH"
            elif "LOW" in val_str:
                status = "LOW"
            return {
                "status": status,
                "is_abnormal": status != "NORMAL",
                "is_critical": False,
                "ref_min": None,
                "ref_max": None
            }

        # Resolve reference bounds
        ref_min, ref_max = self.parse_reference_range(range_str)
        
        # Heuristic fallback if ranges are missing or failed parsing
        if ref_min is None and ref_max is None:
            for kw, bounds in self.DEFAULT_RANGES.items():
                if kw in name_lower:
                    ref_min, ref_max = bounds[0], bounds[1]
                    break

        # Standard evaluations
        status = "NORMAL"
        is_critical = False
        
        # Check critical alarm limits first
        crit_min, crit_max = None, None
        for kw, limits in self.CRITICAL_LIMITS.items():
            if kw in name_lower:
                crit_min, crit_max = limits[0], limits[1]
                break

        if crit_min is not None and numeric_val <= crit_min:
            status = "CRITICAL_LOW"
            is_critical = True
        elif crit_max is not None and numeric_val >= crit_max:
            status = "CRITICAL_HIGH"
            is_critical = True
        else:
            # Evaluate abnormal bounds
            if ref_min is not None and numeric_val < ref_min:
                status = "LOW"
            elif ref_max is not None and numeric_val > ref_max:
                status = "HIGH"

        return {
            "status": status,
            "is_abnormal": status != "NORMAL",
            "is_critical": is_critical,
            "ref_min": ref_min,
            "ref_max": ref_max
        }
