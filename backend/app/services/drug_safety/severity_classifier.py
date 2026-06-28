from typing import List

class SeverityClassifier:
    """Classifies overall drug interaction severity based on the highest detected interaction severity."""

    SEVERITY_ORDER = {
        "HIGH": 4,
        "MEDIUM": 3,
        "LOW": 2,
        "UNKNOWN": 1,
        "NONE": 0
    }

    @classmethod
    def classify(cls, severities: List[str]) -> str:
        """
        Takes a list of severity strings and returns the highest severity found.
        Returns 'NONE' if the list is empty or invalid.
        """
        if not severities:
            return "NONE"
            
        highest_sev = "NONE"
        highest_score = -1
        
        for sev in severities:
            s = sev.upper() if sev else "NONE"
            if s not in cls.SEVERITY_ORDER:
                s = "UNKNOWN"
            score = cls.SEVERITY_ORDER[s]
            if score > highest_score:
                highest_score = score
                highest_sev = s
                
        return highest_sev
