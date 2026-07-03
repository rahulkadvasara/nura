"""
Nura - Chat Execution Service
Orchestrates AI pipeline execution for chat messages, coordinating state and persistence
"""

import time
import logging
from typing import Optional, Dict, Any, List

from app.models.chat import (
    ChatMessageCreate,
    ChatMessageInDB,
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
from app.services.chat_session_service import ChatSessionService
from app.services.chat.context_builder import build_conversation_context
from app.services.multi_agent_orchestrator import MultiAgentOrchestrator

logger = logging.getLogger(__name__)


class ChatExecutionService:
    """Entry point for executing user chat messages through the AI pipeline"""

    def __init__(
        self,
        chat_session_repository: ChatSessionRepository,
        chat_message_repository: ChatMessageRepository,
        chat_message_service: ChatMessageService,
        chat_session_service: ChatSessionService,
        orchestrator: MultiAgentOrchestrator,
        context_resolver = None,
        rich_card_service = None,
    ):
        self.chat_session_repository = chat_session_repository
        self.chat_message_repository = chat_message_repository
        self.chat_message_service = chat_message_service
        self.chat_session_service = chat_session_service
        self.orchestrator = orchestrator

        if context_resolver is None:
            from app.core.dependencies import get_healthcare_context_resolver
            self.context_resolver = get_healthcare_context_resolver()
        else:
            self.context_resolver = context_resolver

        if rich_card_service is None:
            from app.core.dependencies import get_rich_card_service
            self.rich_card_service = get_rich_card_service()
        else:
            self.rich_card_service = rich_card_service

    async def execute_chat_message(
        self,
        session_id: str,
        patient_id: str,
        message: str,
        debug_mode: bool = False
    ) -> ChatExecutionResponse:
        """
        Executes a user message through the Multi-Agent AI Orchestrator:
        1. Validates the session exists and belongs to the patient.
        2. Persists the user message to MongoDB.
        3. Generates the conversation history context.
        4. Runs the Multi-Agent Orchestrator.
        5. Persists the assistant's response to MongoDB.
        6. Updates session statistics (token counts, cost, latencies).
        7. Returns the standardized ChatExecutionResponse.
        """
        # 1. Validation
        session = await self.chat_session_repository.get(session_id)
        if not session or session.status == SessionStatus.DELETED:
            raise ValueError(f"Chat session with ID {session_id} does not exist or has been deleted")
        if session.patient_id != patient_id:
            raise PermissionError(f"Patient {patient_id} is not authorized to access session {session_id}")

        # 2. Persist the User Message
        from app.schemas.chat import ChatMessageCreate as CreateSchema
        user_msg_schema = CreateSchema(
            session_id=session_id,
            patient_id=patient_id,
            role=MessageRole.USER,
            content=message.strip(),
        )
        # Store user message first
        user_msg = await self.chat_message_service.create_message(user_msg_schema)

        # 3. Compile conversation context
        # Retrieve recent session history (excluding current user message to avoid duplicate context query)
        context = await build_conversation_context(
            chat_message_repository=self.chat_message_repository,
            session_id=session_id,
            current_message=message.strip(),
            session_metadata=session.metadata or {},
            limit=20
        )

        # 4. Invoke Multi-Agent AI Orchestrator
        start_time = time.time()
        
        # Build orchestrator execution request
        # Pass conversation context inside request metadata
        orchestrator_req = AIExecuteRequest(
            query=message.strip(),
            patient_id=patient_id,
            session_id=session_id,
            debug_mode=debug_mode,
            metadata={
                "conversation_history": context,
                "chat_session_title": session.title
            }
        )

        # Execute
        contract = await self.orchestrator.execute(orchestrator_req, user_id=patient_id, role="patient")
        latency_ms = (time.time() - start_time) * 1000.0

        if not contract.success:
            # AI Execution failed. We preserve the stored user message and raise an error
            logger.error(f"Orchestrator failed to execute chat message: {contract.response}")
            raise RuntimeError(contract.response or "AI Orchestration failed")

        # 5. Persist Assistant Response
        # Resolve Healthcare Context & Cards
        resolved_ctx = await self.context_resolver.resolve_context(patient_id, message)
        cards = self.rich_card_service.build_cards(resolved_ctx)
        
        # Build actions from cards
        actions = []
        for card in cards:
            actions.extend(card.actions)

        assistant_content = contract.response or "No response generated by assistant."
        assistant_msg_schema = CreateSchema(
            session_id=session_id,
            patient_id=patient_id,
            role=MessageRole.ASSISTANT,
            content=assistant_content,
            citations=contract.citations,
            token_usage=contract.usage,
            latency_ms=int(latency_ms),
            metadata={
                "agent": contract.agent,
                "intent": contract.intent,
                "cost": contract.cost,
                "cards": [card.model_dump() for card in cards],
                "actions": [act.model_dump() for act in actions],
            }
        )
        assistant_msg = await self.chat_message_service.create_message(assistant_msg_schema)

        # 6. Update Parent Session Stats (Tokens & Cumulative Cost)
        # ChatMessageService.create_message already increments session message_count and last_message_at.
        # Here we add cost and last agent metadata.
        sess_update = ChatSessionUpdate(
            total_cost=session.total_cost + contract.cost,
            last_agent_used=contract.agent or "UnknownAgent",
        )
        await self.chat_session_repository.update(session_id, sess_update)

        # Trigger background updates asynchronously
        import asyncio
        async def run_bg_session_updates():
            try:
                from app.core.dependencies import get_memory_update_service
                memory_update_service = get_memory_update_service()
                await memory_update_service.evaluate_and_sync_session(
                    session_id=session_id,
                    patient_id=patient_id,
                    message_ids=[user_msg.id, assistant_msg.id]
                )
            except Exception as bg_err:
                logger.error(f"Background memory sync failed in chat execution: {bg_err}", exc_info=True)

            try:
                from app.core.dependencies import get_conversation_intelligence_service
                intelligence_service = get_conversation_intelligence_service()
                await intelligence_service.auto_update_session_metadata(session_id)
            except Exception as bg_err:
                logger.error(f"Background metadata update failed in chat execution: {bg_err}", exc_info=True)

        asyncio.create_task(run_bg_session_updates())

        # 7. Return Response
        return ChatExecutionResponse(
            assistant_message=assistant_content,
            agent_used=contract.agent,
            citations=contract.citations,
            usage=contract.usage,
            latency_ms=latency_ms,
            cost=contract.cost,
            cards=cards,
            actions=actions,
        )

