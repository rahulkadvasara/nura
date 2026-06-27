"""
Nura - Parsing Utilities for Operational Agent LLM outputs
"""

import re
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("nura.agents.operations.utils")


def parse_llm_json_response(raw_text: str) -> Optional[Dict[str, Any]]:
    """Clean markdown backticks and parse raw text block as JSON"""
    if not raw_text:
        return None

    cleaned = raw_text.strip()
    
    # Remove markdown code block wrappers if present
    if cleaned.startswith("```"):
        # Match ```json ... ``` or ``` ... ```
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to decode LLM response as JSON. Error: {str(e)}. Raw text: {raw_text}")
        # Secondary fallback: try regex lookup of first opening { to closing }
        try:
            match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
            if match:
                return json.loads(match.group(1))
        except Exception:
            pass
        return None
