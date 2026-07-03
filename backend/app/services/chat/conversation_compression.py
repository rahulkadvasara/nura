"""
Nura - Conversation Compression Service
Automatically compresses long message histories when token limits are exceeded.
"""
import logging
from typing import List, Dict, Any
from app.models.chat import ChatMessageInDB, MessageRole

logger = logging.getLogger("nura.chat.compression")


class ConversationCompressionService:
    """Manages history truncation and clinical context compression"""

    def __init__(self, max_tokens: int = 8000, keep_recent_count: int = 6):
        self.max_tokens = max_tokens
        self.keep_recent_count = keep_recent_count

    def estimate_tokens(self, content: str) -> int:
        """Estimate tokens using len(text) // 4 character heuristic"""
        return len(content) // 4

    async def compress_history(self, messages: List[ChatMessageInDB]) -> List[Dict[str, Any]]:
        """
        Compress history to fit max_tokens budget.
        Preserves recent, bookmarked, cited, and clinical messages, compressing others.
        """
        total_tokens = sum(self.estimate_tokens(m.content) for m in messages)
        if total_tokens <= self.max_tokens:
            return self._map_to_history(messages)

        logger.info(f"Conversation exceeds token budget ({total_tokens} > {self.max_tokens}). Compressing...")

        preserved_messages = []
        messages_to_compress = []

        recent_cutoff = len(messages) - self.keep_recent_count

        # Keyword list indicating clinically critical context
        clinical_keywords = [
            "symptom", "pain", "prescribe", "medication", "drug", "allergy",
            "allergic", "diagnose", "diagnosis", "report", "blood", "safety",
            "side effect", "contraindication"
        ]

        for idx, msg in enumerate(messages):
            is_recent = idx >= recent_cutoff
            is_bookmarked = msg.metadata.get("bookmarked") is True if msg.metadata else False
            is_cited = len(msg.citations or []) > 0
            
            content_lower = msg.content.lower()
            has_clinical_context = any(word in content_lower for word in clinical_keywords)

            if is_recent or is_bookmarked or is_cited or has_clinical_context:
                preserved_messages.append(msg)
            else:
                messages_to_compress.append(msg)

        if not messages_to_compress:
            # Everything was clinically important, return original mapped list
            return self._map_to_history(messages)

        # Summarize older, non-essential queries
        summary_chunks = []
        for m in messages_to_compress:
            role_label = "Patient" if m.role == MessageRole.USER else "Assistant"
            summary_chunks.append(f"{role_label}: {m.content}")

        summary_text = " | ".join(summary_chunks)
        if len(summary_text) > 2000:
            summary_text = summary_text[:2000] + "..."

        compressed_system_message = {
            "role": "system",
            "content": f"Context summary of earlier conversation: {summary_text}"
        }

        result = [compressed_system_message]
        result.extend(self._map_to_history(preserved_messages))
        return result

    def _map_to_history(self, messages: List[ChatMessageInDB]) -> List[Dict[str, Any]]:
        history = []
        for msg in messages:
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
        return history


# Global singleton instance
_compression_service_instance = ConversationCompressionService()


def get_conversation_compression_service() -> ConversationCompressionService:
    """Get the global ConversationCompressionService singleton"""
    return _compression_service_instance
