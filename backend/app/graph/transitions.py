"""
Nura - LangGraph Transition Manager
Defines reusable routing transitions, conditional loops, and finish hooks.
"""

from typing import Dict, Callable, List, Optional, Any


class GraphTransition:
    """Represents a connection between source and target nodes in the state graph"""

    def __init__(
        self,
        source: str,
        target: Optional[str] = None,
        transition_type: str = "normal",  # normal, conditional, finish
        condition_func: Optional[Callable[[Any], str]] = None,
        mapping: Optional[Dict[str, str]] = None
    ):
        self.source = source
        self.target = target
        self.transition_type = transition_type
        self.condition_func = condition_func
        self.mapping = mapping or {}


class TransitionManager:
    """Manages normal, conditional, and terminal transitions between nodes"""

    def __init__(self):
        self._transitions: Dict[str, List[GraphTransition]] = {}

    def add_transition(self, source: str, target: str) -> None:
        """Register a normal transition from source to target node"""
        transition = GraphTransition(
            source=source,
            target=target,
            transition_type="normal"
        )
        self._transitions.setdefault(source, []).append(transition)

    def add_conditional_transition(
        self,
        source: str,
        condition_func: Callable[[Any], str],
        mapping: Dict[str, str]
    ) -> None:
        """Register a conditional transition based on a state evaluator logic function"""
        if not callable(condition_func):
            raise TypeError("Conditional evaluator must be a callable function.")
        transition = GraphTransition(
            source=source,
            transition_type="conditional",
            condition_func=condition_func,
            mapping=mapping
        )
        self._transitions.setdefault(source, []).append(transition)

    def add_finish_transition(self, source: str, target: str) -> None:
        """Register a finish transition pointing to final termination node"""
        transition = GraphTransition(
            source=source,
            target=target,
            transition_type="finish"
        )
        self._transitions.setdefault(source, []).append(transition)

    def get_transitions_for(self, source: str) -> List[GraphTransition]:
        """Retrieve all transitions originating from source node"""
        return self._transitions.get(source, [])

    def get_next_node(self, source: str, state: Any) -> Optional[str]:
        """
        Evaluate and return next node name based on current state.
        Returns None if no matching transitions exist.
        """
        transitions = self.get_transitions_for(source)
        if not transitions:
            return None

        # Process first matching transition (or iterate)
        for t in transitions:
            if t.transition_type in ("normal", "finish"):
                return t.target
            elif t.transition_type == "conditional":
                if t.condition_func:
                    # Run condition function with state
                    result_key = t.condition_func(state)
                    # Resolve result key to node ID from mapping
                    return t.mapping.get(result_key)
        return None

    def list_all_transitions(self) -> List[Dict[str, Any]]:
        """Return serialized list of all registered transitions configurations"""
        flat_list = []
        for source, t_list in self._transitions.items():
            for t in t_list:
                flat_list.append({
                    "source": t.source,
                    "target": t.target,
                    "type": t.transition_type,
                    "mapping": t.mapping
                })
        return flat_list

    def clear(self) -> None:
        """Reset all transitions rules"""
        self._transitions.clear()
