"""
Nura Backend - Router Agent Unit Tests
Verifies RouterAgent execution decisions, confidence thresholds, fallbacks, and graph nodes integration.
"""

import pytest
import asyncio
from unittest.mock import MagicMock
from app.agents.router.router_agent import RouterAgent
from app.agents.router.fallback import FallbackManager
from app.graph.state import GraphState
from app.graph.nodes import RouterAgentNode
from app.graph.constants import ROUTER_AGENT_NODE


@pytest.mark.asyncio
async def test_router_agent_execution_decision():
    """Verify RouterAgent classifies query and selects target downstream agent"""
    agent = RouterAgent()
    
    # High confidence medical question
    decision = await agent.run_routing("what causes high cholesterol level disease symptoms?")
    assert decision.detected_intent == "MEDICAL_QUESTION"
    assert decision.selected_agent == "MedicalKnowledgeAgent"
    assert decision.confidence >= 0.5


@pytest.mark.asyncio
async def test_router_agent_ambiguous_fallback():
    """Verify ambiguous queries (identical top intent scores) resolve to UNKNOWN fallback"""
    agent = RouterAgent()
    
    # Query matching both GREETING and DRUG_INTERACTION keywords with equal strength
    # e.g., "Hello, does paracetamol interact?" -> Hello (keyword), paracetamol (keyword)
    decision = await agent.run_routing("Hello recall paracetamol booking")
    # Equal keyword matches across different intents makes classification ambiguous
    # If the scores match, FallbackManager resolves to UNKNOWN
    assert decision.detected_intent == "UNKNOWN"
    assert decision.selected_agent == "UnknownAgent"


@pytest.mark.asyncio
async def test_router_agent_empty_query_fallback():
    """Verify empty query inputs resolve to UNKNOWN fallback"""
    agent = RouterAgent()
    decision = await agent.run_routing("   ")
    assert decision.detected_intent == "UNKNOWN"
    assert decision.selected_agent == "UnknownAgent"
    assert decision.confidence == 0.0


@pytest.mark.asyncio
async def test_router_graph_node_integration():
    """Verify RouterAgentNode execution correctly updates GraphState parameters"""
    node = RouterAgentNode()
    
    state = GraphState(
        query="I need to recommend a good cardiologist specialist near me",
        current_node="initialize_state",
        execution_trace=["__start__", "initialize_state"]
    )
    
    updates = await node(state)
    
    assert updates["current_node"] == ROUTER_AGENT_NODE
    assert updates["previous_node"] == "initialize_state"
    assert updates["detected_intent"] == "DOCTOR_RECOMMENDATION"
    assert updates["selected_agent"] == "DoctorRecommendationAgent"
    assert ROUTER_AGENT_NODE in updates["execution_trace"]
    assert "routing_confidence" in updates["metadata"]
    assert "matched_rules" in updates["metadata"]
