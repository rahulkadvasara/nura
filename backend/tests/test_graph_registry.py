"""
Nura Backend - Graph Registry Unit Tests
Verifies dynamic registration, unregistration, duplicates protection, and types check.
"""

import pytest
from app.graph.registry import NodeRegistry


def test_registry_registration_and_lookup():
    registry = NodeRegistry()
    
    # Define a mock node callable
    async def mock_node(state):
        return {"response": "test"}

    # Register and lookup
    registry.register_node("mock_node", mock_node)
    assert "mock_node" in registry.list_nodes()
    
    resolved = registry.lookup_node("mock_node")
    assert resolved == mock_node


def test_registry_prevents_duplicate_names():
    registry = NodeRegistry()
    
    async def mock_node1(state): return {}
    async def mock_node2(state): return {}

    registry.register_node("node", mock_node1)
    
    with pytest.raises(ValueError) as excinfo:
        registry.register_node("node", mock_node2)
    assert "already registered" in str(excinfo.value)


def test_registry_prevents_non_callable():
    registry = NodeRegistry()
    
    with pytest.raises(TypeError):
        registry.register_node("invalid", "not-a-callable")


def test_registry_unregistration():
    registry = NodeRegistry()
    async def mock_node(state): return {}
    
    registry.register_node("node", mock_node)
    assert "node" in registry.list_nodes()
    
    registry.unregister_node("node")
    assert "node" not in registry.list_nodes()
    
    with pytest.raises(KeyError):
        registry.lookup_node("node")
