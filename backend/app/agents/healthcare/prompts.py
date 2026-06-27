"""
Nura - Healthcare Agents Prompt Helpers
Initializes PromptLoader for healthcare agents templates.
"""

from app.prompts.loader import PromptLoader

# Initialize global prompt loader reference
prompt_loader = PromptLoader()


def get_healthcare_prompt(name: str, is_system: bool = False) -> str:
    """Fetch prompt template by name"""
    return prompt_loader.get_template(name, is_system)


def render_healthcare_prompt(name: str, variables: dict, is_system: bool = False) -> str:
    """Render prompt template substituting placeholder variables"""
    return prompt_loader.render(name, variables, is_system)
