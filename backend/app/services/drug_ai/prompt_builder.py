import os
from typing import Dict, Any, List
from app.prompts.loader import PromptLoader

class DrugPromptLoader(PromptLoader):
    """Reuses PromptLoader to retrieve template paths directly under backend/app/prompts/drug"""

    def __init__(self):
        base_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "prompts",
            "drug"
        )
        super().__init__(base_path=base_path)

    def get_template(self, name: str, is_system: bool = False) -> str:
        """Fetch prompt from backend/app/prompts/drug/name.md"""
        cache_key = f"drug:{name}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        file_path = os.path.join(self.base_path, f"{name}.md")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Prompt template file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.cache[cache_key] = content
        return content


class DrugPromptBuilder:
    """Builder to render prompts using DrugPromptLoader with correct placeholders"""

    def __init__(self, loader: DrugPromptLoader):
        self.loader = loader

    def build_patient_explanation(
        self,
        medications: List[str],
        severity: str,
        recommendations: List[str],
        interactions: List[Dict[str, Any]]
    ) -> str:
        vars_dict = {
            "incoming_medications": ", ".join(medications),
            "severity": severity,
            "recommendations": "; ".join(recommendations),
            "interactions": self._format_interactions(interactions)
        }
        return self.loader.render("patient_explanation", vars_dict)

    def build_doctor_explanation(
        self,
        medications: List[str],
        severity: str,
        recommendations: List[str],
        interactions: List[Dict[str, Any]]
    ) -> str:
        vars_dict = {
            "incoming_medications": ", ".join(medications),
            "severity": severity,
            "recommendations": "; ".join(recommendations),
            "interactions": self._format_interactions(interactions)
        }
        return self.loader.render("doctor_explanation", vars_dict)

    def build_interaction_summary(
        self,
        medications: List[str],
        severity: str,
        recommendations: List[str],
        interactions: List[Dict[str, Any]]
    ) -> str:
        vars_dict = {
            "incoming_medications": ", ".join(medications),
            "severity": severity,
            "recommendations": "; ".join(recommendations),
            "interactions": self._format_interactions(interactions)
        }
        return self.loader.render("interaction_summary", vars_dict)

    def build_medication_precautions(
        self,
        medications: List[str],
        severity: str,
        recommendations: List[str],
        interactions: List[Dict[str, Any]]
    ) -> str:
        vars_dict = {
            "incoming_medications": ", ".join(medications),
            "severity": severity,
            "recommendations": "; ".join(recommendations),
            "interactions": self._format_interactions(interactions)
        }
        return self.loader.render("medication_precautions", vars_dict)

    def _format_interactions(self, interactions: List[Dict[str, Any]]) -> str:
        if not interactions:
            return "No interactions detected."
        lines = []
        for p in interactions:
            lines.append(
                f"- Drug A: {p.get('drug_a')} ({p.get('drug_a_normalized')}), "
                f"Drug B: {p.get('drug_b')} ({p.get('drug_b_normalized')}), "
                f"Severity: {p.get('severity')}. Description: {p.get('description')}"
            )
        return "\n".join(lines)
