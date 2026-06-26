"""
Nura - Memory Agent Base
"""
from typing import Optional, List, Dict, Any
from app.agents.base.base_agent import BaseAgent
from app.agents.base.context import AgentContext

class MemoryAgent(BaseAgent):
    """Base agent providing interfaces for longitudinal memory, semantic memory, and conversation history retrieval"""

    def __init__(self, name: str = "Memory Agent", settings=None):
        super().__init__(name=name, settings=settings)

    async def get_patient_memory(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve patient longitudinal memory profile. Subclasses should override this."""
        self.logger.info(f"Memory interface: get_patient_memory called for patient_id='{patient_id}'")
        return None

    async def update_patient_memory(self, patient_id: str, updates: Dict[str, Any]) -> bool:
        """Update patient longitudinal memory profile. Subclasses should override this."""
        self.logger.info(f"Memory interface: update_patient_memory called for patient_id='{patient_id}'")
        return False

    async def get_conversation_history(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve historical messages from conversation memory. Subclasses should override this."""
        self.logger.info(f"Memory interface: get_conversation_history called for session_id='{session_id}'")
        return []

    async def execute(self, input_data: Any, context: Optional[AgentContext] = None) -> Any:
        """Default execute method for MemoryAgent."""
        patient_id = context.patient_id if context else None
        memory = None
        if patient_id:
            memory = await self.get_patient_memory(patient_id)
        return {
            "response": memory,
            "citations": [f"memory://patient/{patient_id}"] if patient_id else [],
            "metadata": {"has_memory": memory is not None}
        }
