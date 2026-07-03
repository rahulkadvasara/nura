"""
Nura - Chat Feedback Service
Manages user feedback (Helpful / Not Helpful) on assistant responses
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.chat_message_repository import ChatMessageRepository

logger = logging.getLogger(__name__)


class FeedbackService:
    """Stores patient feedback for assistant answers in a separate audit collection"""

    def __init__(self, db: AsyncIOMotorDatabase, chat_message_repository: ChatMessageRepository):
        self.db = db
        self.chat_message_repository = chat_message_repository

    async def submit_feedback(
        self,
        message_id: str,
        patient_id: str,
        rating: str,
        comment: Optional[str] = None
    ) -> bool:
        """
        Stores user feedback (Helpful/Not Helpful) in the chat_feedbacks collection.
        Validates message existence and user permission before storing.
        """
        # Validate message exists
        msg = await self.chat_message_repository.get(message_id)
        if not msg:
            raise ValueError("Message not found")
        if msg.patient_id != patient_id:
            raise PermissionError("Not authorized to submit feedback for this message")

        feedback_doc = {
            "message_id": message_id,
            "patient_id": patient_id,
            "rating": rating,  # "helpful" or "unhelpful"
            "comment": comment.strip() if comment else None,
            "timestamp": datetime.now(timezone.utc)
        }

        try:
            await self.db.chat_feedbacks.insert_one(feedback_doc)
            logger.info(f"Feedback successfully recorded for message: {message_id}")
            return True
        except Exception as e:
            logger.exception(f"Failed to save user feedback: {e}")
            return False
