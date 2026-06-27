"""
Nura - Router Intent Registry
Dynamic registry mapping intent classifications to downstream AI execution agents.
"""

from typing import Dict, Optional


class IntentRegistry:
    """Registry directory mapping categorized user intents to target downstream execution agents"""

    def __init__(self):
        self._mappings: Dict[str, str] = {}
        self._initialize_defaults()

    def _initialize_defaults(self) -> None:
        """Load default intent-to-agent mapping configurations"""
        self._mappings = {
            "GREETING": "GreetingAgent",
            "GENERAL_CHAT": "GeneralChatAgent",
            "MEDICAL_QUESTION": "MedicalKnowledgeAgent",
            "SYMPTOM_ANALYSIS": "SymptomAgent",
            "REPORT_ANALYSIS": "ReportAnalysisAgent",
            "DRUG_INTERACTION": "DrugInteractionAgent",
            "DOCTOR_RECOMMENDATION": "DoctorRecommendationAgent",
            "REMINDER": "ReminderAgent",
            "APPOINTMENT": "AppointmentAgent",
            "CONVERSATION_RECALL": "ConversationRecallAgent",
            "UNKNOWN": "UnknownAgent"
        }

    def register_intent(self, intent: str, agent_name: str) -> None:
        """Register a new downstream agent mapping for an intent key. Prevents duplicates registration."""
        upper_intent = intent.upper().strip()
        if upper_intent in self._mappings:
            raise ValueError(
                f"Duplicate mapping error: Intent '{upper_intent}' is already mapped to agent '{self._mappings[upper_intent]}'."
            )
        if not agent_name or not agent_name.strip():
            raise ValueError("Target agent name cannot be empty.")
        self._mappings[upper_intent] = agent_name

    def get_agent(self, intent: str) -> Optional[str]:
        """Retrieve target downstream agent mapped for given intent key"""
        return self._mappings.get(intent.upper().strip())

    def list_mappings(self) -> Dict[str, str]:
        """Return copy of active mappings list"""
        return dict(self._mappings)

    def clear(self) -> None:
        """Reset registry mapping configurations back to defaults"""
        self._initialize_defaults()


# Global Singleton instance
_registry_instance = IntentRegistry()


def get_intent_registry() -> IntentRegistry:
    """Retrieve singleton instance of IntentRegistry"""
    return _registry_instance
