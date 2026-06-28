import re

class DrugNormalizer:
    """Service to normalize drug names deterministically by removing dosage values and forms."""

    # Regex to match dosage strengths: e.g. 500mg, 650 mg, 1.5ml, 10%, 100u, 50 iu
    STRENGTH_REGEX = re.compile(
        r'\b\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|iu|units?|u)\b|\b\d+(?:\.\d+)?\s*%', 
        re.IGNORECASE
    )
    
    # Regex to match standalone numbers: e.g. 500, 10 (which are usually strengths without unit)
    STANDALONE_NUMBER_REGEX = re.compile(
        r'\b\d+(?:\.\d+)?\b'
    )
    
    # Regex to match common dosage forms: tablet, capsules, etc.
    FORM_REGEX = re.compile(
        r'\b(?:tablets?|capsules?|tabs?|caps?|injections?|inj|oral|suspension|solutions?|cream|ointment|gel|sprays?|liquid)\b',
        re.IGNORECASE
    )

    @classmethod
    def normalize(cls, name: str) -> str:
        """
        Normalize a drug name deterministically.
        Rules:
        - lowercase
        - strip dosage strengths (e.g. 500mg, 1%)
        - strip standalone numbers (e.g. 500)
        - strip dosage forms (e.g. tablet, capsules)
        - trim whitespace
        - deduplicate internal spaces
        """
        if not name:
            return ""
            
        # 1. Lowercase
        normalized = name.lower()
        
        # 2. Remove dosage strengths (e.g., "650mg")
        normalized = cls.STRENGTH_REGEX.sub(" ", normalized)
        
        # 3. Remove standalone numbers (e.g., "500" in "metformin 500")
        normalized = cls.STANDALONE_NUMBER_REGEX.sub(" ", normalized)
        
        # 4. Remove common dosage forms (e.g., "tablet")
        normalized = cls.FORM_REGEX.sub(" ", normalized)
        
        # 5. Clean up duplicate spaces and trim boundaries
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
