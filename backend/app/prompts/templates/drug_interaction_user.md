Assembled Patient Memory & Profile:
{patient_context}

Assembled Drug Safety Knowledge Reference:
{retrieved_context}

User Drug Query:
{query}

Format your output as a valid JSON object matching this schema:
{{
  "interaction_found": true,
  "severity": "LOW, MEDIUM, HIGH, or CRITICAL",
  "interaction_summary": "Summary of detected drug safety issues, warnings, and safety disclaimers",
  "warnings": ["Warning details A", "Warning details B"],
  "alternatives": ["Suggested alternatives or discussion points to bring to the physician"]
}}
Do not add any text before or after the JSON structure.
