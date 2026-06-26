"""
Nura - Prompt Template Loader
"""
import os
import re
from typing import Dict, Any, Optional, Set

class PromptLoader:
    """Loader and validation registry for AI prompt templates"""

    def __init__(self, base_path: Optional[str] = None):
        if base_path is None:
            base_path = os.path.dirname(os.path.abspath(__file__))
        self.base_path = base_path
        self.cache: Dict[str, str] = {}
        self.versions: Dict[str, str] = {
            "base_system_prompt": "1.0.0",
            "medical_assistant": "1.0.0",
            "report_analysis": "1.0.0",
            "chat_prompt": "1.0.0",
            "report_prompt": "1.0.0",
            "drug_prompt": "1.0.0",
            "summary_prompt": "1.0.0",
        }

    def get_template(self, name: str, is_system: bool = False) -> str:
        """Fetch template content from cache or disk"""
        cache_key = f"{'system' if is_system else 'template'}:{name}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        sub_dir = "system" if is_system else "templates"
        file_path = os.path.join(self.base_path, sub_dir, f"{name}.md")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Prompt template file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.cache[cache_key] = content
        return content

    def get_placeholders(self, template: str) -> Set[str]:
        """Extract placeholder keys using regex avoiding double braces (JSON)"""
        return set(re.findall(r"(?<!\{)\{([a-zA-Z0-9_]+)\}(?!\})", template))

    def validate_placeholders(self, template: str, variables: Dict[str, Any]) -> None:
        """Validate that all template placeholders are supplied in variables dict"""
        placeholders = self.get_placeholders(template)
        missing = [p for p in placeholders if p not in variables]
        if missing:
            raise ValueError(f"Missing required prompt placeholders: {missing}")

    def render(self, name: str, variables: Dict[str, Any], is_system: bool = False) -> str:
        """Validate placeholders and replace variables in prompt template"""
        template = self.get_template(name, is_system)
        self.validate_placeholders(template, variables)
        rendered = template
        for k, v in variables.items():
            rendered = rendered.replace(f"{{{k}}}", str(v))
        return rendered

    def get_version(self, name: str) -> str:
        """Return registry version of the template"""
        return self.versions.get(name, "1.0.0")
