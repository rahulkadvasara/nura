"""
Nura - Medical Extraction Normalizer
"""

import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("nura.report_extraction.normalizer")


class MedicalNormalizer:
    """Standardizes extracted medical properties, formats dates, and merges clinical entries duplicates"""

    def normalize_date(self, date_str: Optional[str]) -> Optional[str]:
        """Convert standard date formats to YYYY-MM-DD format.
        
        Supports inputs like:
        - "12-Jan-2024" or "12 Jan 2024"
        - "12/01/2024" or "01/12/2024"
        """
        if not date_str:
            return None
        
        val = date_str.strip()
        
        # Try finding YYYY-MM-DD pattern directly
        match = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", val)
        if match:
            return f"{match.group(1)}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"
            
        # Try DD/MM/YYYY or MM/DD/YYYY
        match = re.search(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", val)
        if match:
            # Safely assume DD-MM-YYYY
            return f"{match.group(3)}-{int(match.group(2)):02d}-{int(match.group(1)):02d}"

        # Alpha month match: "12 Jan 2024" or "12-Jan-2024"
        months = {
            "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
            "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
        }
        month_pattern = "|".join(months.keys())
        match = re.search(rf"(\d{{1,2}})[\s\-_,]+({month_pattern})[\s\-_,]+(\d{{4}})", val, re.IGNORECASE)
        if match:
            m_num = months[match.group(2).lower()[:3]]
            return f"{match.group(3)}-{m_num:02d}-{int(match.group(1)):02d}"

        return val

    def normalize_unit(self, unit_str: Optional[str]) -> Optional[str]:
        """Normalize laboratory result units (e.g. g/dl -> g/dL)"""
        if not unit_str:
            return None
        val = unit_str.strip().lower()
        
        mapping = {
            "g/dl": "g/dL",
            "g/l": "g/L",
            "mg/dl": "mg/dL",
            "mg/l": "mg/L",
            "u/l": "U/L",
            "iu/l": "IU/L",
            "mmol/l": "mmol/L",
            "k/ul": "k/uL",
            "k/cumm": "k/cumm",
            "cells/ul": "cells/uL",
            "pg": "pg",
            "fl": "fL",
            "t/l": "T/L"
        }
        return mapping.get(val, unit_str)

    def normalize_status(self, status_str: Optional[str]) -> str:
        """Normalize laboratory result status strings (e.g. high -> HIGH)"""
        if not status_str:
            return "NORMAL"
        val = status_str.strip().upper()
        if val in ("NORMAL", "HIGH", "LOW", "ABNORMAL"):
            return val
        if "HIGH" in val:
            return "HIGH"
        if "LOW" in val:
            return "LOW"
        if "ABNORMAL" in val or "ERR" in val:
            return "ABNORMAL"
        return "NORMAL"

    def merge_diagnoses(self, diagnoses: List[str]) -> List[str]:
        """Consolidates identical and near-identical diagnoses strings (case-insensitive deduplication)"""
        seen = set()
        merged = []
        for d in diagnoses:
            clean = d.strip().lower()
            if not clean:
                continue
            # Remove minor punctuation variants
            clean = re.sub(r"[^\w\s]", "", clean)
            if clean not in seen:
                seen.add(clean)
                merged.append(d.strip())
        return merged

    def merge_allergies(self, allergies: List[str]) -> List[str]:
        """Consolidates allergies arrays"""
        seen = set()
        merged = []
        for a in allergies:
            clean = a.strip().lower()
            if not clean:
                continue
            if clean not in seen:
                seen.add(clean)
                merged.append(a.strip())
        return merged
