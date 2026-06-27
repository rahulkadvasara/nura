"""
Nura - Core Agents Utilities
Helper functions for formatting, parsing, and cleaning responses.
"""

import re
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("nura.agents.core.utils")


def clean_json_response(content: str) -> Optional[Dict[str, Any]]:
    """
    Cleans LLM response text, stripping markdown code block fences
    and extracting the first valid JSON block.
    """
    if not content or not content.strip():
        return None
        
    cleaned = content.strip()
    
    # 1. Strip markdown json code block fences if present
    # Matches ```json { ... } ``` or ``` { ... } ```
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL | re.IGNORECASE)
    if match:
        cleaned = match.group(1).strip()
        
    # 2. Try parsing directly
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
        
    # 3. If direct parsing fails, extract substring between first '{' and last '}'
    try:
        start_idx = cleaned.find("{")
        end_idx = cleaned.rfind("}")
        if start_idx != -1 and end_idx != -1:
            json_str = cleaned[start_idx:end_idx + 1]
            return json.loads(json_str)
    except Exception as e:
        logger.error(f"Failed to parse or clean JSON response: {str(e)}", exc_info=True)
        
    return None
