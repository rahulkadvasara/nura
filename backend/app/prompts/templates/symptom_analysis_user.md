Assembled Patient Profile:
{patient_context}

Assembled Medical Knowledge Reference:
{retrieved_context}

User Symptoms Query:
{query}

Format your output as a valid JSON object matching this schema:
{{
  "summary": "Professional summary of the symptoms and safety notice disclaimer",
  "possible_causes": ["Cause A", "Cause B"],
  "red_flags": ["Red Flag A", "Red Flag B"],
  "recommended_action": "Action steps, home care or doctor visit suggestions",
  "emergency": false
}}
Do not add any text before or after the JSON structure.
