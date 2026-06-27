"""
Nura - LangGraph Node Registry
Dynamic registration and lookup directory for orchestrator workflow nodes.
"""

from typing import Dict, Callable, List, Optional


class NodeRegistry:
    """Dynamic registry directory managing registered nodes callable references"""

    def __init__(self):
        self._nodes: Dict[str, Callable] = {}

    def register_node(self, name: str, node_callable: Callable) -> None:
        """Register a new workflow node callback. Prevents duplicates registration."""
        if name in self._nodes:
            raise ValueError(f"Node with name '{name}' is already registered in registry.")
        if not callable(node_callable):
            raise TypeError("Registered node must be a callable function or class instance.")
        self._nodes[name] = node_callable

    def unregister_node(self, name: str) -> None:
        """Remove a node callback reference from the registry"""
        if name in self._nodes:
            del self._nodes[name]

    def lookup_node(self, name: str) -> Callable:
        """Retrieve node callback reference. Raises KeyError if not found."""
        if name not in self._nodes:
            raise KeyError(f"Node '{name}' is not registered in registry.")
        return self._nodes[name]

    def list_nodes(self) -> List[str]:
        """Return list of all registered node names"""
        return list(self._nodes.keys())

    def clear(self) -> None:
        """Reset registry mappings"""
        self._nodes.clear()


# Global Singleton instance
_registry_instance: Optional[NodeRegistry] = None


def get_graph_registry() -> NodeRegistry:
    """Retrieve singleton instance of NodeRegistry"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = NodeRegistry()
    return _registry_instance
