Assembled Patient Context & Profile:
{patient_context}

Available Doctors Profiles:
{retrieved_context}

User Query or Symptoms:
{query}

Format your output as a valid JSON object matching this schema:
{{
  "recommended_doctors": [
    {{
      "doctor_id": "MongoDB ID of doctor profile",
      "full_name": "Doctor full name",
      "specialization": "Doctor specialty",
      "hospital": "Hospital affiliation",
      "experience_years": 10,
      "languages": ["English", "Spanish"],
      "availability": "Available slots summary or notice if none",
      "match_reason": "Specific clinical reason why this doctor matches the symptoms and query"
    }}
  ],
  "reasoning": "Overall match summary reasoning",
  "matching_specialization": "The primarily matched doctor specialization category",
  "confidence": 0.95
}}
Do not add any text before or after the JSON structure.
