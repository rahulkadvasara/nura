"""
Nura - Conversation Context Builder
Prepares conversation context window from MongoDB history for Multi-Agent execution
"""

import logging
from typing import List, Dict, Any
from app.repositories.chat_message_repository import ChatMessageRepository

logger = logging.getLogger(__name__)


async def build_conversation_context(
    chat_message_repository: ChatMessageRepository,
    session_id: str,
    current_message: str,
    session_metadata: Dict[str, Any],
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Retrieves the last `limit` messages from MongoDB and formats them as a list of dicts:
    [{"role": "user"|"assistant"|"system", "content": "..."}]
    Includes session metadata as system context if present, and returns the list.
    """
    try:
        # 1. Fetch recent messages sorted chronologically (ascending)
        # Note: get_by_session_id returns messages sorted by created_at (ascending)
        messages = await chat_message_repository.get_by_session_id(
            session_id=session_id,
            limit=limit,
            skip=0,
            include_deleted=False
        )

        history: List[Dict[str, Any]] = []

        # 2. Format history
        for msg in messages:
            # Map database role to string roles for LangGraph/LLM
            role_val = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
            role_str = "user"
            if role_val == "ASSISTANT":
                role_str = "assistant"
            elif role_val == "SYSTEM":
                role_str = "system"

            history.append({
                "role": role_str,
                "content": msg.content
            })

        # 3. Add system metadata instruction at the top if present
        if session_metadata:
            # Inject a system prompt reflecting session metadata (e.g. topic, description)
            description = session_metadata.get("description")
            if description:
                history.insert(0, {
                    "role": "system",
                    "content": f"Context: This conversation concerns: {description}"
                })

        return history
    except Exception as e:
        logger.error(f"Error compiling conversation context: {e}", exc_info=True)
        return []
