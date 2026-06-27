"""
Nura - LangGraph Workflow Builder
Coordinates node registration, transitions linkage, validation, and compilation.
"""

import logging
from typing import Dict, Any, List, Optional
from app.graph.registry import NodeRegistry, get_graph_registry
from app.graph.transitions import TransitionManager
from app.graph.constants import START_NODE, FINISH_NODE
from app.graph.engine import LangGraphEngine

logger = logging.getLogger("nura.graph.builder")


class GraphBuilder:
    """Builder class responsible for structuring nodes/transitions and compiling the graph engine"""

    def __init__(
        self,
        registry: NodeRegistry = None,
        transition_manager: TransitionManager = None
    ):
        self.registry = registry or get_graph_registry()
        self.transitions = transition_manager or TransitionManager()
        self._compiled_engine: Optional[LangGraphEngine] = None

    def add_node(self, name: str, node_callable: Any) -> None:
        """Register a node callable to the builder's registry"""
        self.registry.register_node(name, node_callable)
        # Clear compiled engine if graph changes
        self._compiled_engine = None

    def add_transition(self, source: str, target: str) -> None:
        """Link source node directly to target node"""
        self.transitions.add_transition(source, target)
        self._compiled_engine = None

    def add_conditional_transition(
        self,
        source: str,
        condition_func: Any,
        mapping: Dict[str, str]
    ) -> None:
        """Link source node conditionally using an evaluator mapping"""
        self.transitions.add_conditional_transition(source, condition_func, mapping)
        self._compiled_engine = None

    def validate_graph(self) -> bool:
        """
        Validate graph connectivity.
        1. Checks that START_NODE and FINISH_NODE exist.
        2. Asserts a path connection exists from START_NODE reaching FINISH_NODE.
        """
        registered = self.registry.list_nodes()
        if START_NODE not in registered:
            logger.error(f"Graph validation failed: START_NODE '{START_NODE}' is not registered.")
            return False
        if FINISH_NODE not in registered:
            logger.error(f"Graph validation failed: FINISH_NODE '{FINISH_NODE}' is not registered.")
            return False

        # Verify reachability of FINISH_NODE from START_NODE using BFS
        visited = set()
        queue = [START_NODE]
        
        while queue:
            curr = queue.pop(0)
            if curr == FINISH_NODE:
                return True
            if curr not in visited:
                visited.add(curr)
                # Find all target nodes from transitions out of curr
                next_targets = []
                for t in self.transitions.get_transitions_for(curr):
                    if t.transition_type in ("normal", "finish") and t.target:
                        next_targets.append(t.target)
                    elif t.transition_type == "conditional" and t.mapping:
                        next_targets.extend(t.mapping.values())
                        
                for target in next_targets:
                    if target in registered and target not in visited:
                        queue.append(target)
                        
        logger.error("Graph validation failed: FINISH_NODE is unreachable from START_NODE.")
        return False

    def compile(self) -> LangGraphEngine:
        """
        Compile the state graph structure.
        Graph validation and compilation only executes once, caching the compiled instance.
        """
        if self._compiled_engine is not None:
            return self._compiled_engine

        # Validate graph layout structure
        if not self.validate_graph():
            raise ValueError("Cannot compile graph: structure layout validation failed.")

        # Compile and cache the engine instance
        self._compiled_engine = LangGraphEngine(
            registry=self.registry,
            transitions=self.transitions
        )
        logger.info("LangGraph orchestration engine compiled successfully.")
        return self._compiled_engine


# Global Singleton instance
_builder_instance: Optional[GraphBuilder] = None


def get_graph_builder() -> GraphBuilder:
    """Retrieve singleton instance of GraphBuilder"""
    global _builder_instance
    if _builder_instance is None:
        _builder_instance = GraphBuilder()
    return _builder_instance
