"""
Nura Backend - Graph Engine Unit Tests
Verifies sync/async runs, state updates merging, path traces, retries, and timeout boundaries.
"""

import pytest
import asyncio
import time
from typing import Dict, Any
from app.graph.builder import GraphBuilder
from app.graph.registry import NodeRegistry
from app.graph.transitions import TransitionManager
from app.graph.state import GraphState
from app.graph.constants import START_NODE, FINISH_NODE
from app.graph.telemetry import GraphTelemetryTracker
from app.core.ai_config import ai_settings

# Mark all tests in this file as async
pytestmark = pytest.mark.asyncio


async def test_engine_successful_execution():
    registry = NodeRegistry()
    transitions = TransitionManager()
    telemetry = GraphTelemetryTracker()
    builder = GraphBuilder(registry=registry, transition_manager=transitions)

    # Setup mock nodes
    async def start_node_fn(state: GraphState) -> Dict[str, Any]:
        return {"current_node": START_NODE, "execution_trace": [START_NODE]}

    async def mid_node_fn(state: GraphState) -> Dict[str, Any]:
        trace = list(state.execution_trace) + ["mid"]
        return {"execution_trace": trace, "response": "hello from mid"}

    async def finish_node_fn(state: GraphState) -> Dict[str, Any]:
        trace = list(state.execution_trace) + [FINISH_NODE]
        return {"execution_trace": trace, "response": state.response + " completed"}

    registry.register_node(START_NODE, start_node_fn)
    registry.register_node("mid", mid_node_fn)
    registry.register_node(FINISH_NODE, finish_node_fn)

    transitions.add_transition(START_NODE, "mid")
    transitions.add_transition("mid", FINISH_NODE)

    builder._compiled_engine = None  # reset
    engine = builder.compile()
    engine.telemetry = telemetry

    initial_state = {"query": "test query"}
    result = await engine.execute_async(initial_state)

    assert result["error"] is None
    assert result["response"] == "hello from mid completed"
    assert result["execution_trace"] == [START_NODE, "mid", FINISH_NODE]
    assert telemetry.successful_executions == 1
    assert telemetry.total_executions == 1
    assert telemetry.node_execution_count[START_NODE] == 1
    assert telemetry.node_execution_count["mid"] == 1
    assert telemetry.node_execution_count[FINISH_NODE] == 1


async def test_engine_conditional_routing():
    registry = NodeRegistry()
    transitions = TransitionManager()
    builder = GraphBuilder(registry=registry, transition_manager=transitions)

    async def start_fn(state): return {"execution_trace": [START_NODE]}
    async def left_fn(state): return {"response": "left", "execution_trace": list(state.execution_trace) + ["left"]}
    async def right_fn(state): return {"response": "right", "execution_trace": list(state.execution_trace) + ["right"]}
    async def finish_fn(state): return {"execution_trace": list(state.execution_trace) + [FINISH_NODE]}

    registry.register_node(START_NODE, start_fn)
    registry.register_node("left", left_fn)
    registry.register_node("right", right_fn)
    registry.register_node(FINISH_NODE, finish_fn)

    # Route based on query content
    def condition_fn(state: GraphState) -> str:
        if state.query == "go left":
            return "l"
        return "r"

    transitions.add_conditional_transition(
        START_NODE,
        condition_fn,
        {"l": "left", "r": "right"}
    )
    transitions.add_transition("left", FINISH_NODE)
    transitions.add_transition("right", FINISH_NODE)

    engine = builder.compile()

    # Test left path
    res_left = await engine.execute_async({"query": "go left"})
    assert "left" in res_left["execution_trace"]
    assert res_left["response"] == "left"

    # Test right path
    res_right = await engine.execute_async({"query": "go right"})
    assert "right" in res_right["execution_trace"]
    assert res_right["response"] == "right"


async def test_engine_node_execution_retries():
    registry = NodeRegistry()
    transitions = TransitionManager()
    builder = GraphBuilder(registry=registry, transition_manager=transitions)

    call_count = 0

    async def start_fn(state): return {"execution_trace": [START_NODE]}
    
    async def failing_node_fn(state):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Intermittent mock error")
        return {"response": "recovered", "execution_trace": list(state.execution_trace) + ["mid"]}
        
    async def finish_fn(state): return {"execution_trace": list(state.execution_trace) + [FINISH_NODE]}

    registry.register_node(START_NODE, start_fn)
    registry.register_node("mid", failing_node_fn)
    registry.register_node(FINISH_NODE, finish_fn)

    transitions.add_transition(START_NODE, "mid")
    transitions.add_transition("mid", FINISH_NODE)

    engine = builder.compile()
    
    # Configure configuration settings to allow retries
    ai_settings.GRAPH_MAX_RETRIES = 3

    result = await engine.execute_async({})
    assert result["error"] is None
    assert result["response"] == "recovered"
    assert call_count == 3  # Failed twice, succeeded on 3rd attempt


async def test_engine_execution_timeout():
    registry = NodeRegistry()
    transitions = TransitionManager()
    builder = GraphBuilder(registry=registry, transition_manager=transitions)

    async def start_fn(state): return {"execution_trace": [START_NODE]}
    
    async def slow_node_fn(state):
        await asyncio.sleep(0.5)  # longer than GRAPH_TIMEOUT
        return {"response": "done"}
        
    async def finish_fn(state): return {"execution_trace": list(state.execution_trace) + [FINISH_NODE]}

    registry.register_node(START_NODE, start_fn)
    registry.register_node("slow", slow_node_fn)
    registry.register_node(FINISH_NODE, finish_fn)

    transitions.add_transition(START_NODE, "slow")
    transitions.add_transition("slow", FINISH_NODE)

    engine = builder.compile()
    
    # Configure tiny timeout
    old_timeout = ai_settings.GRAPH_TIMEOUT
    ai_settings.GRAPH_TIMEOUT = 0.1
    
    try:
        result = await engine.execute_async({})
        assert "timed out" in result["error"]
        assert engine.telemetry.timeout_count == 1
    finally:
        ai_settings.GRAPH_TIMEOUT = old_timeout
