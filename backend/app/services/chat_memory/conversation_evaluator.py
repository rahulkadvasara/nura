"""
Nura - Conversation Evaluator Service
Evaluates chat session worthiness for memories
"""

import logging
from typing import Dict, Any

from app.repositories.chat_message_repository import ChatMessageRepository
from app.services.chat_memory.memory_rules import evaluate_conversation_deterministically
from app.services.chat_memory.telemetry import memory_telemetry

logger = logging.getLogger(__name__)


class ConversationEvaluator:
    """Coordinates conversation worthiness evaluations and metrics logging"""

    def __init__(self, chat_message_repository: ChatMessageRepository):
        self.chat_message_repository = chat_message_repository

    async def evaluate_session(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieves all non-deleted messages for the session, runs the deterministic
        rules evaluator, records statistics, and returns the scoring block.
        """
        messages = await self.chat_message_repository.get_by_session_id(
            session_id=session_id,
            limit=200,
            skip=0,
            include_deleted=False
        )

        formatted = [
            {
                "role": m.role.value if hasattr(m.role, "value") else str(m.role),
                "content": m.content
            }
            for m in messages
        ]
        
        # Evaluate
        eval_result = evaluate_conversation_deterministically(formatted)

        # Record telemetry
        memory_telemetry.record_evaluation(
            eval_result["memory_score"],
            eval_result["semantic_score"],
            eval_result["clinical_score"],
            eval_result["should_store_chat_memory"],
            eval_result["should_update_patient_memory"]
        )

        return eval_result
