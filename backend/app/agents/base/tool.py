"""
Nura - Tool Abstraction
"""
from abc import ABC, abstractmethod
from typing import Dict, Any

class Tool(ABC):
    """Abstract base class for all tools utilized by platform agents"""

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """Execute the primary tool action logic asynchronously"""
        pass

    def validate(self, *args, **kwargs) -> bool:
        """Validate input arguments before tool execution. Override if custom schema validation is needed."""
        return True

    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """Return the documentation and schema definition metadata for the tool"""
        pass
