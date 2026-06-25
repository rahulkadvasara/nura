"""
Nura - Agent Log Service
Business logic and operations for AI agent execution logs
"""

from datetime import datetime, timezone
from typing import List, Optional

from app.models.observability import (
    AgentLogCreate,
    AgentLogUpdate,
    AgentLogInDB,
    AgentLogStatus,
)
from app.schemas.observability import (
    AgentLogCreateSchema,
    AgentLogUpdateSchema,
    AgentLogResponse,
)
from app.repositories.agent_log_repository import AgentLogRepository
from app.services.base import BaseService


def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


def _log_to_response(log: AgentLogInDB) -> AgentLogResponse:
    return AgentLogResponse(
        id=log.id,
        agent_name=log.agent_name,
        workflow_id=log.workflow_id,
        session_id=log.session_id,
        patient_id=log.patient_id,
        user_id=log.user_id,
        input_payload=log.input_payload,
        output_payload=log.output_payload,
        status=log.status,
        latency_ms=log.latency_ms,
        token_usage=log.token_usage,
        error_message=log.error_message,
        langgraph_thread_id=log.langgraph_thread_id,
        langgraph_checkpoint_id=log.langgraph_checkpoint_id,
        langfuse_trace_id=log.langfuse_trace_id,
        langfuse_parent_observation_id=log.langfuse_parent_observation_id,
        orchestrator_node=log.orchestrator_node,
        evaluation_metrics=log.evaluation_metrics,
        research_metadata=log.research_metadata,
        created_at=log.created_at,
    )


class AgentLogService(BaseService[AgentLogInDB, AgentLogCreate, AgentLogUpdate]):
    """Service layer for agent log operations"""

    def __init__(self, agent_log_repository: AgentLogRepository):
        super().__init__()
        self.agent_log_repository = agent_log_repository

    async def create_log(
        self,
        schema: AgentLogCreateSchema,
    ) -> AgentLogInDB:
        """Create a new agent log record"""
        now = utc_now()
        log_create = AgentLogCreate(
            agent_name=schema.agent_name,
            workflow_id=schema.workflow_id,
            session_id=schema.session_id,
            patient_id=schema.patient_id,
            user_id=schema.user_id,
            input_payload=schema.input_payload,
            output_payload=schema.output_payload or {},
            status=schema.status,
            latency_ms=schema.latency_ms,
            token_usage=schema.token_usage or {},
            error_message=schema.error_message,
            langgraph_thread_id=schema.langgraph_thread_id,
            langgraph_checkpoint_id=schema.langgraph_checkpoint_id,
            langfuse_trace_id=schema.langfuse_trace_id,
            langfuse_parent_observation_id=schema.langfuse_parent_observation_id,
            orchestrator_node=schema.orchestrator_node,
            evaluation_metrics=schema.evaluation_metrics or {},
            research_metadata=schema.research_metadata or {},
        )

        doc_dict = log_create.model_dump()
        doc_dict["created_at"] = now

        result = await self.agent_log_repository.collection.insert_one(doc_dict)
        created = await self.agent_log_repository.collection.find_one({"_id": result.inserted_id})
        if created is None:
            raise RuntimeError("Agent log was inserted but could not be retrieved")
        return AgentLogInDB.from_mongo(created)

    async def get_log_by_id(self, log_id: str) -> Optional[AgentLogInDB]:
        """Fetch an agent log by its ID"""
        return await self.agent_log_repository.get(log_id)

    async def list_logs(self, limit: int = 100, skip: int = 0) -> List[AgentLogInDB]:
        """List all agent logs"""
        return await self.agent_log_repository.list(limit=limit, skip=skip)

    async def list_logs_by_agent(
        self,
        agent_name: str,
        limit: int = 100,
        skip: int = 0,
    ) -> List[AgentLogInDB]:
        """Fetch logs for an agent"""
        return await self.agent_log_repository.get_by_agent(agent_name, limit=limit, skip=skip)

    async def list_logs_by_workflow(
        self,
        workflow_id: str,
        limit: int = 100,
        skip: int = 0,
    ) -> List[AgentLogInDB]:
        """Fetch logs for a workflow execution ID"""
        return await self.agent_log_repository.get_by_workflow(workflow_id, limit=limit, skip=skip)

    async def list_failed_runs(self, limit: int = 100, skip: int = 0) -> List[AgentLogInDB]:
        """Fetch failed agent executions"""
        return await self.agent_log_repository.get_failed_runs(limit=limit, skip=skip)

    async def update_log(
        self,
        log_id: str,
        schema: AgentLogUpdateSchema,
    ) -> Optional[AgentLogInDB]:
        """Update an existing agent log record"""
        update = AgentLogUpdate(**schema.model_dump(exclude_unset=True))
        return await self.agent_log_repository.update(log_id, update)

    async def delete_log(self, log_id: str) -> bool:
        """Permanently delete an agent log record"""
        return await self.agent_log_repository.delete(log_id)

    def to_response(self, log: AgentLogInDB) -> AgentLogResponse:
        """Convert internal model to API response"""
        return _log_to_response(log)

    async def get_agent_logs_paginated(
        self,
        limit: int = 50,
        skip: int = 0,
        agent: Optional[str] = None,
        status: Optional[str] = None,
        session: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> tuple[List[AgentLogInDB], int]:
        """Fetch agent execution logs matching parameters dynamically"""
        query = {}
        
        if agent:
            query["agent_name"] = agent
            
        if status:
            query["status"] = status
            
        if session:
            query["session_id"] = session

        if start_date or end_date:
            date_query = {}
            if start_date:
                try:
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
                    date_query["$gte"] = start_dt
                except ValueError:
                    pass
            if end_date:
                try:
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc)
                    date_query["$lte"] = end_dt
                except ValueError:
                    pass
            if date_query:
                query["created_at"] = date_query

        total = await self.agent_log_repository.collection.count_documents(query)
        cursor = self.agent_log_repository.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        logs = [AgentLogInDB.from_mongo(doc) for doc in await cursor.to_list(length=limit)]

        return logs, total

