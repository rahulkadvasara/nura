Assembled Patient Profile:
{patient_context}

Assembled Medical Knowledge Reference:
{retrieved_context}

User Symptoms Query:
{query}

Format your output as a valid JSON object matching this schema:
{{
  "risk_level": "LOW | MODERATE | HIGH | CRITICAL",
  "summary": "Clinical evaluation of the symptoms and possible physiological mechanisms",
  "possible_causes": ["Cause A", "Cause B"],
  "red_flags": ["Red Flag A", "Red Flag B"],
  "recommended_action": "Doctor-like recommended action (e.g. Home care, Consult GP within 24-48 hrs, Consult Specialist, or Emergency ER care)",
  "emergency": false
}}
Do not add any text before or after the JSON structure.
