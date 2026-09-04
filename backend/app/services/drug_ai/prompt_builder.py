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

    def _format_interactions(self, interactions: List[Any]) -> str:
        if not interactions:
            return "No interactions detected."
        lines = []
        for p in interactions:
            d_a = p.get('drug_a') if isinstance(p, dict) else getattr(p, 'drug_a', '')
            d_a_norm = p.get('drug_a_normalized') if isinstance(p, dict) else getattr(p, 'drug_a_normalized', '')
            d_b = p.get('drug_b') if isinstance(p, dict) else getattr(p, 'drug_b', '')
            d_b_norm = p.get('drug_b_normalized') if isinstance(p, dict) else getattr(p, 'drug_b_normalized', '')
            sev = p.get('severity') if isinstance(p, dict) else getattr(p, 'severity', '')
            desc = p.get('description') if isinstance(p, dict) else getattr(p, 'description', '')
            lines.append(
                f"- Drug A: {d_a} ({d_a_norm}), "
                f"Drug B: {d_b} ({d_b_norm}), "
                f"Severity: {sev}. Description: {desc}"
            )
        return "\n".join(lines)
