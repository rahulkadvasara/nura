"""
Nura - Regeneration Service
Handles response regeneration of the latest assistant message, maintaining history and session metrics
"""

import time
import logging
from typing import Optional

from app.models.chat import (
    ChatMessageUpdate,
    MessageRole,
    ChatSessionUpdate,
    SessionStatus,
)
from app.schemas.chat import (
    ChatExecutionResponse,
)
from app.schemas.orchestrator import AIExecuteRequest
from app.repositories.chat_session_repository import ChatSessionRepository
from app.repositories.chat_message_repository import ChatMessageRepository
from app.services.chat_message_service import ChatMessageService
from app.services.chat.context_builder import build_conversation_context
from app.services.multi_agent_orchestrator import MultiAgentOrchestrator

logger = logging.getLogger(__name__)


class RegenerationService:
    """Manages AI assistant response regeneration flows"""

    def __init__(
        self,
        chat_session_repository: ChatSessionRepository,
        chat_message_repository: ChatMessageRepository,
        chat_message_service: ChatMessageService,
        orchestrator: MultiAgentOrchestrator,
    ):
        self.chat_session_repository = chat_session_repository
        self.chat_message_repository = chat_message_repository
        self.chat_message_service = chat_message_service
        self.orchestrator = orchestrator

    async def regenerate_latest_response(
        self,
        session_id: str,
        patient_id: str,
        debug_mode: bool = False
    ) -> ChatExecutionResponse:
        """
        Locates the latest assistant message, soft-deletes it, offsets session counts/costs,
        re-runs the orchestrator on the user message query, and saves the new response.
        """
        # 1. Validation
        session = await self.chat_session_repository.get(session_id)
        if not session or session.status == SessionStatus.DELETED:
            raise ValueError("Session not found or deleted")
        if session.patient_id != patient_id:
            raise PermissionError("Access forbidden to this session")

        # 2. Find the last assistant message and preceding user message
        # Fetch last 10 messages chronologically to search
        messages = await self.chat_message_repository.get_by_session_id(
            session_id=session_id,
            limit=10,
            skip=0,
            include_deleted=False
        )

        if not messages:
            raise ValueError("No conversation history found to regenerate")

        # Find latest assistant message
        old_assistant_msg = None
        user_msg = None
        
        # Traverse backwards
        for i in range(len(messages) - 1, -1, -1):
            if messages[i].role == MessageRole.ASSISTANT:
                old_assistant_msg = messages[i]
                # Preceding message should be a USER message
                if i > 0 and messages[i-1].role == MessageRole.USER:
                    user_msg = messages[i-1]
                break

        if not old_assistant_msg:
            raise ValueError("No assistant response found to regenerate")
        if not user_msg:
            raise ValueError("No user query found to regenerate response for")

        # 3. Soft-delete the previous assistant message
        await self.chat_message_service.delete_message(old_assistant_msg.id)

        # 4. Offset previous assistant stats in session
        old_tokens = old_assistant_msg.token_usage.get("total_tokens", 0)
        old_cost = old_assistant_msg.metadata.get("cost", 0.0) if old_assistant_msg.metadata else 0.0

        # Retrieve refreshed session state to deduct correctly
        refreshed_session = await self.chat_session_repository.get(session_id)
        current_tokens = refreshed_session.total_tokens if refreshed_session else session.total_tokens
        current_cost = refreshed_session.total_cost if refreshed_session else session.total_cost
        current_count = refreshed_session.message_count if refreshed_session else session.message_count

        offset_update = ChatSessionUpdate(
            message_count=max(0, current_count - 1),
            total_tokens=max(0, current_tokens - old_tokens),
            total_cost=max(0.0, current_cost - old_cost)
        )
        await self.chat_session_repository.update(session_id, offset_update)

        # 5. Compile context (excluding the soft-deleted assistant response)
        context = await build_conversation_context(
            chat_message_repository=self.chat_message_repository,
            session_id=session_id,
            current_message=user_msg.content,
            session_metadata=session.metadata or {},
            limit=20
        )

        # 6. Execute Orchestrator
        start_time = time.time()
        orchestrator_req = AIExecuteRequest(
            query=user_msg.content,
            patient_id=patient_id,
            session_id=session_id,
            debug_mode=debug_mode,
            metadata={
                "conversation_history": context,
                "chat_session_title": session.title,
                "regeneration": True
            }
        )

        contract = await self.orchestrator.execute(orchestrator_req, user_id=patient_id, role="patient")
        latency_ms = (time.time() - start_time) * 1000.0

        if not contract.success:
            logger.error(f"Orchestrator failed during response regeneration: {contract.response}")
            raise RuntimeError(contract.response or "Regeneration failed")

        # 7. Persist the newly generated assistant message
        # Maintain internal regeneration history in metadata
        old_metadata = old_assistant_msg.metadata or {}
        old_regen_count = old_metadata.get("regeneration_count", 0)

        from app.schemas.chat import ChatMessageCreate as CreateSchema
        assistant_msg_schema = CreateSchema(
            session_id=session_id,
            patient_id=patient_id,
            role=MessageRole.ASSISTANT,
            content=contract.response or "No response generated.",
            citations=contract.citations,
            token_usage=contract.usage,
            latency_ms=int(latency_ms),
            metadata={
                "agent": contract.agent,
                "intent": contract.intent,
                "cost": contract.cost,
                "replaced_message_id": old_assistant_msg.id,
                "regeneration_count": old_regen_count + 1
            }
        )
        new_assistant_msg = await self.chat_message_service.create_message(assistant_msg_schema)

        # Refetch final session details to update cost & agent
        final_session = await self.chat_session_repository.get(session_id)
        final_cost = final_session.total_cost if final_session else session.total_cost
        
        final_update = ChatSessionUpdate(
            total_cost=final_cost + contract.cost,
            last_agent_used=contract.agent or "UnknownAgent"
        )
        await self.chat_session_repository.update(session_id, final_update)

        return ChatExecutionResponse(
            assistant_message=new_assistant_msg.content,
            agent_used=contract.agent,
            citations=contract.citations,
            usage=contract.usage,
            latency_ms=latency_ms,
            cost=contract.cost
        )
