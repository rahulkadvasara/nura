"""
Nura - Retrieval Agent Base
"""
from typing import Optional, List, Dict, Any
from app.agents.base.base_agent import BaseAgent
from app.agents.base.context import AgentContext

class RetrievalAgent(BaseAgent):
    """Base agent containing reusable retrieval interfaces and hooks for vector/knowledge search"""

    def __init__(self, name: str = "Retrieval Agent", settings=None):
        super().__init__(name=name, settings=settings)

    async def retrieve(self, query: str, collection: str, limit: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Abstract retrieval interface.
        Subclasses should override this method to perform vector database or context search.
        """
        self.logger.info(f"Retrieval interface called with query='{query}' for collection='{collection}'")
        return []

    async def execute(self, input_data: Any, context: Optional[AgentContext] = None) -> Any:
        """Default execute block for retrieval, yielding an empty search results list."""
        query = str(input_data)
        collection = context.metadata.get("collection", "general") if context else "general"
        results = await self.retrieve(query, collection=collection)
        return {
            "response": results,
            "citations": [f"retrieval://{collection}?q={query}"],
            "metadata": {"results_count": len(results)}
        }
