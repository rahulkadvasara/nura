"""
Nura - Chat Telemetry Service
Calculates real-time usage statistics for sessions and messages from MongoDB
"""

import logging
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.chat import SessionStatus

logger = logging.getLogger(__name__)


async def get_chat_statistics(db: AsyncIOMotorDatabase) -> dict:
    """
    Fetch consolidated telemetry metrics for chat sessions and messages.
    Returns a dictionary matching the ChatStatisticsResponse schema.
    """
    try:
        # 1. Chat Sessions metrics
        sessions_created = await db.chat_sessions.count_documents({})
        sessions_archived = await db.chat_sessions.count_documents({"status": SessionStatus.ARCHIVED})
        sessions_deleted = await db.chat_sessions.count_documents({"status": SessionStatus.DELETED})

        # 2. Chat Messages metrics
        messages_created = await db.chat_messages.count_documents({})
        messages_edited = await db.chat_messages.count_documents({"edited_at": {"$ne": None}})
        messages_deleted = await db.chat_messages.count_documents({"deleted": True})

        # 3. Aggregates
        average_messages_per_session = 0.0
        if sessions_created > 0:
            average_messages_per_session = round(messages_created / sessions_created, 2)

        return {
            "sessions_created": sessions_created,
            "sessions_archived": sessions_archived,
            "sessions_deleted": sessions_deleted,
            "messages_created": messages_created,
            "messages_edited": messages_edited,
            "messages_deleted": messages_deleted,
            "average_messages_per_session": average_messages_per_session
        }
    except Exception as e:
        logger.error(f"Error fetching chat telemetry statistics: {e}", exc_info=True)
        return {
            "sessions_created": 0,
            "sessions_archived": 0,
            "sessions_deleted": 0,
            "messages_created": 0,
            "messages_edited": 0,
            "messages_deleted": 0,
            "average_messages_per_session": 0.0
        }
