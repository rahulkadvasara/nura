"""
Nura Backend - Graph Builder Unit Tests
Verifies links layout validations, reachability checkers, and compiler caching logic.
"""

import pytest
from app.graph.builder import GraphBuilder
from app.graph.registry import NodeRegistry
from app.graph.transitions import TransitionManager
from app.graph.constants import START_NODE, FINISH_NODE


def test_builder_fails_missing_gateways():
    registry = NodeRegistry()
    transitions = TransitionManager()
    builder = GraphBuilder(registry=registry, transition_manager=transitions)

    # Empty registry
    assert builder.validate_graph() is False

    # Start only
    registry.register_node(START_NODE, lambda x: {})
    assert builder.validate_graph() is False


def test_builder_fails_unreachable_finish():
    registry = NodeRegistry()
    transitions = TransitionManager()
    builder = GraphBuilder(registry=registry, transition_manager=transitions)

    registry.register_node(START_NODE, lambda x: {})
    registry.register_node(FINISH_NODE, lambda x: {})
    registry.register_node("isolated_node", lambda x: {})

    # No transitions at all
    assert builder.validate_graph() is False

    # Isolated path
    transitions.add_transition(START_NODE, "isolated_node")
    assert builder.validate_graph() is False


def test_builder_success_reachable_path():
    registry = NodeRegistry()
    transitions = TransitionManager()
    builder = GraphBuilder(registry=registry, transition_manager=transitions)

    registry.register_node(START_NODE, lambda x: {})
    registry.register_node("node1", lambda x: {})
    registry.register_node(FINISH_NODE, lambda x: {})

    transitions.add_transition(START_NODE, "node1")
    transitions.add_transition("node1", FINISH_NODE)

    assert builder.validate_graph() is True
    
    # Verify compilation works
    engine = builder.compile()
    assert engine is not None
    
    # Caching compiled engine
    engine2 = builder.compile()
    assert engine is engine2
