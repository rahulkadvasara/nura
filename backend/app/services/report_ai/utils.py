"""
Nura - Prompt Loader for report summarization prompts
"""

import os
from app.prompts.loader import PromptLoader


class ReportPromptLoader(PromptLoader):
    """Reuses PromptLoader to retrieve template paths directly under backend/app/prompts/report"""

    def __init__(self):
        # Resolve to backend/app/prompts/report
        base_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "app",
            "prompts",
            "report"
        )
        super().__init__(base_path=base_path)

    def get_template(self, name: str, is_system: bool = False) -> str:
        """Fetch prompt from backend/app/prompts/report/name.md"""
        cache_key = f"report:{name}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        file_path = os.path.join(self.base_path, f"{name}.md")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Prompt template file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.cache[cache_key] = content
        return content
