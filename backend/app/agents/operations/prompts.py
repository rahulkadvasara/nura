"""
Nura - Prompts Rendering Helpers for Operational Agents
"""

from typing import Dict, Any
from app.prompts.loader import PromptLoader


def render_reminder_prompts(
    loader: PromptLoader,
    variables: Dict[str, Any]
) -> tuple[str, str]:
    """Helper to render reminder system and user template prompts"""
    system = loader.get_template("reminder_system", is_system=True)
    user = loader.render("reminder_user", variables, is_system=False)
    return system, user


def render_appointment_prompts(
    loader: PromptLoader,
    variables: Dict[str, Any]
) -> tuple[str, str]:
    """Helper to render appointment system and user template prompts"""
    system = loader.get_template("appointment_system", is_system=True)
    user = loader.render("appointment_user", variables, is_system=False)
    return system, user
