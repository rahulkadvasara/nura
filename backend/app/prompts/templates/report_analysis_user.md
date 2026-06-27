Assembled Patient Profile:
{patient_context}

Assembled Medical Reports Reference:
{retrieved_context}

User Query about Reports:
{query}

Format your output as a valid JSON object matching this schema:
{{
  "summary": "Clear, patient-friendly summary of the medical reports and findings",
  "key_findings": ["Key finding 1", "Key finding 2"],
  "abnormal_values": [
    {{
      "metric": "Name of lab metric (e.g. LDL Cholesterol)",
      "value": "Observed value from report",
      "normal_range": "Standard normal reference range",
      "status": "high, low, or abnormal description"
    }}
  ],
  "trend_analysis": ["Historical trend details comparing recent to older results if available"],
  "recommendations": ["Safe, informational recommendations and next steps for the patient"]
}}
Do not add any text before or after the JSON structure.
