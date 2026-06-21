"""
Nura - Agent Log Repository
MongoDB repository for agent_logs collection
"""

from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection

from app.models.observability import AgentLogCreate, AgentLogUpdate, AgentLogInDB, AgentLogStatus
from app.repositories.base import BaseRepository


class AgentLogRepository(BaseRepository[AgentLogInDB, AgentLogCreate, AgentLogUpdate]):
    """Repository for agent_logs collection"""

    def __init__(self, collection: AsyncIOMotorCollection):
        super().__init__(collection, AgentLogInDB)

    async def get_by_id(self, id: str) -> Optional[AgentLogInDB]:
        """Fetch an agent log record by its ID"""
        return await self.get(id)

    async def list(self, limit: int = 100, skip: int = 0) -> List[AgentLogInDB]:
        """List all agent log records"""
        return await self.get_many({}, limit=limit, skip=skip)

    async def get_by_agent(self, agent_name: str, limit: int = 100, skip: int = 0) -> List[AgentLogInDB]:
        """Fetch logs for a specific agent name"""
        return await self.get_many({"agent_name": agent_name}, limit=limit, skip=skip)

    async def get_by_workflow(self, workflow_id: str, limit: int = 100, skip: int = 0) -> List[AgentLogInDB]:
        """Fetch logs for a specific workflow execution ID"""
        return await self.get_many({"workflow_id": workflow_id}, limit=limit, skip=skip)

    async def get_failed_runs(self, limit: int = 100, skip: int = 0) -> List[AgentLogInDB]:
        """Fetch failed agent executions"""
        return await self.get_many({"status": AgentLogStatus.FAILED}, limit=limit, skip=skip)
