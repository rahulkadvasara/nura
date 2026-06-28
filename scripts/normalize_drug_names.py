import re

def normalize_drug_name(name: str) -> str:
    """
    Normalizes a drug name by:
    1. Converting to lowercase.
    2. Removing all content inside parentheses (e.g. (topical), (3350 with electrolytes)).
    3. Removing punctuation (except spaces and hyphens).
    4. Collapsing multiple spaces.
    5. Stripping leading/trailing whitespace.
    """
    if not name:
        return ""
    
    # Lowercase
    name = name.lower()
    
    # Remove content in parentheses
    name = re.sub(r'\(.*?\)', '', name)
    
    # Remove punctuation except spaces and hyphens
    name = re.sub(r'[^a-z0-9\s-]', ' ', name)
    
    # Collapse multiple spaces and strip
    name = re.sub(r'\s+', ' ', name)
    return name.strip()
