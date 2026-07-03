"""
Nura - Chat Streaming Service
Handles real-time SSE stream delivery of orchestrator messages
"""

import time
import asyncio
import logging
from typing import AsyncGenerator

from app.models.chat import (
    ChatMessageCreate,
    MessageRole,
    ChatSessionUpdate,
    SessionStatus,
)
from app.schemas.chat import ChatStreamChunk
from app.schemas.orchestrator import AIExecuteRequest
from app.repositories.chat_session_repository import ChatSessionRepository
from app.repositories.chat_message_repository import ChatMessageRepository
from app.services.chat_message_service import ChatMessageService
from app.services.chat_session_service import ChatSessionService
from app.services.chat.context_builder import build_conversation_context
from app.services.multi_agent_orchestrator import MultiAgentOrchestrator

logger = logging.getLogger(__name__)


class ChatStreamingService:
    """Orchestrates token-by-token message streaming via Server-Sent Events"""

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

    async def _retrieve_contexts_in_parallel(self, patient_id: str, message: str) -> None:
        """Prefetch relevant context blocks in parallel to warm RAG caches"""
        import asyncio
        from app.agents.base.context import AgentContext
        
        async def fetch_patient_memory():
            try:
                from app.core.dependencies import get_patient_memory_repository
                repo = get_patient_memory_repository()
                await repo.get_by_patient_id(patient_id)
            except Exception as e:
                logger.warning(f"Parallel fetch patient memory failed: {e}")

        async def fetch_vector_intent(intent_name: str):
            try:
                from app.core.dependencies import get_retrieval_agent
                agent = get_retrieval_agent()
                ctx = AgentContext(patient_id=patient_id, metadata={"intent": intent_name, "top_k": 3})
                await agent.execute(message, ctx)
            except Exception as e:
                logger.warning(f"Parallel pre-fetch vector intent {intent_name} failed: {e}")

        intents = ["conversation_recall", "report_analysis", "general_health", "drug_question"]
        await asyncio.gather(
            fetch_patient_memory(),
            *(fetch_vector_intent(intent) for intent in intents)
        )

    async def stream_chat_message(
        self,
        session_id: str,
        patient_id: str,
        message: str,
        debug_mode: bool = False
    ) -> AsyncGenerator[str, None]:
        """
        Runs the Multi-Agent Orchestrator and yields chunks formatted as SSE data streams.
        Gracefully handles cancellation and buffers the finalized text to store at the end.
        """
        # 1. Rate Limiting Check
        from app.services.chat.rate_limiter import get_rate_limiter
        if not get_rate_limiter().is_allowed(patient_id):
            err_chunk = ChatStreamChunk(type="error", error="Too many requests. Please try again later.")
            yield f"data: {err_chunk.model_dump_json()}\n\n"
            return

        # 2. Cache Lookup
        from app.services.chat.cache_service import get_chat_cache_service
        cache_svc = get_chat_cache_service()
        cached_val = cache_svc.get("prompt", f"{session_id}:{message.strip()}")

        from app.services.chat.telemetry_service import get_extended_telemetry
        telemetry = get_extended_telemetry()

        if cached_val is not None:
            telemetry.record_cache(hit=True)
            telemetry.record_stream(event_type="start")
            
            chunk_size = 4
            for i in range(0, len(cached_val.assistant_message), chunk_size):
                chunk = cached_val.assistant_message[i:i+chunk_size]
                tok_chunk = ChatStreamChunk(type="token", content=chunk)
                yield f"data: {tok_chunk.model_dump_json()}\n\n"
                await asyncio.sleep(0.01)

            meta_chunk = ChatStreamChunk(
                type="metadata",
                agent_used=cached_val.agent_used,
                citations=cached_val.citations,
                usage=cached_val.usage,
                latency_ms=0,
                cost=cached_val.cost,
                cards=cached_val.cards,
                actions=cached_val.actions,
            )
            yield f"data: {meta_chunk.model_dump_json()}\n\n"
            telemetry.record_stream(event_type="complete", duration_ms=0.0)
            return

        telemetry.record_cache(hit=False)
        telemetry.record_stream(event_type="start")

        # 3. Validation
        session = await self.chat_session_repository.get(session_id)
        if not session or session.status == SessionStatus.DELETED:
            err_chunk = ChatStreamChunk(type="error", error="Session not found or deleted")
            yield f"data: {err_chunk.model_dump_json()}\n\n"
            telemetry.record_stream(event_type="fail")
            return
        if session.patient_id != patient_id:
            err_chunk = ChatStreamChunk(type="error", error="Forbidden access to session")
            yield f"data: {err_chunk.model_dump_json()}\n\n"
            telemetry.record_stream(event_type="fail")
            return

        # 4. Parallel Pre-Retrieval Optimization
        start_retrieval = time.time()
        await self._retrieve_contexts_in_parallel(patient_id, message)
        telemetry.retrieval_latency += (time.time() - start_retrieval) * 1000.0

        # 5. Persist User Message
        from app.schemas.chat import ChatMessageCreate as CreateSchema
        user_msg_schema = CreateSchema(
            session_id=session_id,
            patient_id=patient_id,
            role=MessageRole.USER,
            content=message.strip(),
        )
        user_msg = await self.chat_message_service.create_message(user_msg_schema)
        cache_svc.invalidate_by_session(session_id)

        # Yield stream initiation token
        init_chunk = ChatStreamChunk(type="token", content="")
        yield f"data: {init_chunk.model_dump_json()}\n\n"

        # 6. Compress Conversation History
        raw_messages = await self.chat_message_repository.get_by_session_id(
            session_id=session_id,
            limit=50,
            skip=0,
            include_deleted=False
        )
        from app.services.chat.conversation_compression import get_conversation_compression_service
        compress_svc = get_conversation_compression_service()
        context = await compress_svc.compress_history(raw_messages)

        # 7. Invoke Multi-Agent Orchestrator
        start_time = time.time()
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

        try:
            contract = await self.orchestrator.execute(orchestrator_req, user_id=patient_id, role="patient")
            latency_ms = (time.time() - start_time) * 1000.0

            if not contract.success:
                err_chunk = ChatStreamChunk(type="error", error=contract.response or "AI Orchestration failed")
                yield f"data: {err_chunk.model_dump_json()}\n\n"
                telemetry.record_stream(event_type="fail")
                return

            response_text = contract.response or "No response generated by assistant."

            # Yield chunks formatted as SSE
            chunk_size = 4
            for i in range(0, len(response_text), chunk_size):
                if asyncio.current_task() and asyncio.current_task().cancelled():
                    telemetry.record_stream(event_type="cancel")
                    raise asyncio.CancelledError()

                chunk = response_text[i:i+chunk_size]
                tok_chunk = ChatStreamChunk(type="token", content=chunk)
                yield f"data: {tok_chunk.model_dump_json()}\n\n"
                await asyncio.sleep(0.01)

            # 8. Resolve Healthcare Context & Cards
            resolved_ctx = await self.context_resolver.resolve_context(patient_id, message)
            cards = self.rich_card_service.build_cards(resolved_ctx)
            
            actions = []
            for card in cards:
                actions.extend(card.actions)

            assistant_msg_schema = CreateSchema(
                session_id=session_id,
                patient_id=patient_id,
                role=MessageRole.ASSISTANT,
                content=response_text,
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
            cache_svc.invalidate_by_session(session_id)

            # Update parent session stats
            sess_update = ChatSessionUpdate(
                total_cost=session.total_cost + contract.cost,
                last_agent_used=contract.agent or "UnknownAgent",
            )
            await self.chat_session_repository.update(session_id, sess_update)

            # 9. Record Telemetry
            telemetry.record_run(
                latency_ms=latency_ms,
                p_tokens=contract.usage.get("prompt_tokens", 0),
                c_tokens=contract.usage.get("completion_tokens", 0),
                cost=contract.cost
            )
            telemetry.record_healthcare(
                cards_count=len(cards),
                citations_count=len(contract.citations),
                follow_ups_count=3
            )
            telemetry.record_stream(event_type="complete", duration_ms=latency_ms)

            # 10. Defer updates to Background Tasks Manager
            from app.services.chat.background_tasks import get_background_task_manager
            bg_mgr = get_background_task_manager()

            async def run_bg_session_updates():
                try:
                    from app.core.dependencies import get_memory_update_service
                    memory_update_service = get_memory_update_service()
                    res = await memory_update_service.evaluate_and_sync_session(
                        session_id=session_id,
                        patient_id=patient_id,
                        message_ids=[user_msg.id, assistant_msg.id]
                    )
                    if res:
                        telemetry.record_memory(
                            eval_sync=res.get("should_store_chat_memory", False),
                            qdrant_store=res.get("should_store_chat_memory", False),
                            patient_update=res.get("should_update_patient_memory", False)
                        )
                except Exception as bg_err:
                    logger.error(f"Background memory sync failed in streaming: {bg_err}", exc_info=True)

                try:
                    from app.core.dependencies import get_conversation_intelligence_service
                    intelligence_service = get_conversation_intelligence_service()
                    await intelligence_service.auto_update_session_metadata(session_id)
                except Exception as bg_err:
                    logger.error(f"Background metadata update failed in streaming: {bg_err}", exc_info=True)

            bg_mgr.run_task(f"memory-sync-{session_id}", run_bg_session_updates())

            # Cache completed payload
            from app.schemas.chat import ChatExecutionResponse
            response_payload = ChatExecutionResponse(
                assistant_message=response_text,
                agent_used=contract.agent,
                citations=contract.citations,
                usage=contract.usage,
                latency_ms=latency_ms,
                cost=contract.cost,
                cards=cards,
                actions=actions,
            )
            cache_svc.set("prompt", f"{session_id}:{message.strip()}", response_payload)

            # 11. Yield final metadata payload
            meta_chunk = ChatStreamChunk(
                type="metadata",
                agent_used=contract.agent,
                citations=contract.citations,
                usage=contract.usage,
                latency_ms=latency_ms,
                cost=contract.cost,
                cards=cards,
                actions=actions,
            )
            yield f"data: {meta_chunk.model_dump_json()}\n\n"

        except asyncio.CancelledError:
            logger.warning(f"SSE client stream cancelled or disconnected for session: {session_id}")
            telemetry.record_stream(event_type="cancel")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in chat streaming service: {e}")
            telemetry.record_stream(event_type="fail")
            err_chunk = ChatStreamChunk(type="error", error=f"Internal Server Error: {str(e)}")
            yield f"data: {err_chunk.model_dump_json()}\n\n"
