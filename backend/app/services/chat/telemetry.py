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
    Returns a dictionary matching the ChatStatisticsResponse schema, extended with AI metrics.
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

        # 4. AI Specific Metrics
        ai_requests = await db.chat_messages.count_documents({"role": "ASSISTANT", "deleted": {"$ne": True}})

        # Retrieve failures from the orchestrator telemetry tracker singleton
        from app.services.multi_agent_orchestrator import get_multi_agent_telemetry
        failures = get_multi_agent_telemetry().failures

        # Aggregate tokens, latency, cost
        token_pipeline = [
            {"$match": {"role": "ASSISTANT", "deleted": {"$ne": True}}},
            {"$group": {
                "_id": None,
                "total_prompt_tokens": {"$sum": "$token_usage.prompt_tokens"},
                "total_completion_tokens": {"$sum": "$token_usage.completion_tokens"},
                "total_tokens": {"$sum": "$token_usage.total_tokens"},
                "avg_latency": {"$avg": "$latency_ms"},
                "total_cost": {"$sum": "$metadata.cost"},
                "avg_response_len": {"$avg": {"$strLenCP": "$content"}}
            }}
        ]
        agg_res = await db.chat_messages.aggregate(token_pipeline).to_list(1)

        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        average_latency = 0.0
        total_cost = 0.0
        average_response_length = 0.0

        if agg_res:
            prompt_tokens = agg_res[0].get("total_prompt_tokens", 0)
            completion_tokens = agg_res[0].get("total_completion_tokens", 0)
            total_tokens = agg_res[0].get("total_tokens", 0)
            average_latency = round(agg_res[0].get("avg_latency", 0.0) or 0.0, 2)
            total_cost = round(agg_res[0].get("total_cost", 0.0) or 0.0, 4)
            average_response_length = round(agg_res[0].get("avg_response_len", 0.0) or 0.0, 2)

        # Agent distribution
        agent_pipeline = [
            {"$match": {"role": "ASSISTANT", "metadata.agent": {"$ne": None}, "deleted": {"$ne": True}}},
            {"$group": {
                "_id": "$metadata.agent",
                "count": {"$sum": 1}
            }}
        ]
        agent_res = await db.chat_messages.aggregate(agent_pipeline).to_list(100)
        agent_distribution = {item["_id"]: item["count"] for item in agent_res}

        return {
            "sessions_created": sessions_created,
            "sessions_archived": sessions_archived,
            "sessions_deleted": sessions_deleted,
            "messages_created": messages_created,
            "messages_edited": messages_edited,
            "messages_deleted": messages_deleted,
            "average_messages_per_session": average_messages_per_session,
            "ai_requests": ai_requests,
            "failures": failures,
            "agent_distribution": agent_distribution,
            "average_latency": average_latency,
            "token_usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            },
            "estimated_cost": total_cost,
            "average_response_length": average_response_length
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
            "average_messages_per_session": 0.0,
            "ai_requests": 0,
            "failures": 0,
            "agent_distribution": {},
            "average_latency": 0.0,
            "token_usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            },
            "estimated_cost": 0.0,
            "average_response_length": 0.0
        }
