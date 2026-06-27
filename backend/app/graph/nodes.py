"""
Nura - LangGraph Infrastructure Nodes
Infrastructure callables executing startup, initialization, router placeholder, and completion.
"""

import time
import uuid
from typing import Dict, Any
from app.graph.state import GraphState
from app.graph.constants import START_NODE, INIT_STATE_NODE, ROUTER_AGENT_NODE, FINISH_NODE


class StartNode:
    """Starting gateway node initiating graph execution log trace"""

    async def __call__(self, state: GraphState) -> Dict[str, Any]:
        trace = list(state.execution_trace) if state.execution_trace else []
        trace.append(START_NODE)
        return {
            "current_node": START_NODE,
            "previous_node": None,
            "execution_trace": trace
        }


class InitializeStateNode:
    """Prepares and validates base workflow state variables (request_id, timestamps, defaults)"""

    async def __call__(self, state: GraphState) -> Dict[str, Any]:
        trace = list(state.execution_trace) if state.execution_trace else []
        trace.append(INIT_STATE_NODE)
        
        updates: Dict[str, Any] = {
            "current_node": INIT_STATE_NODE,
            "previous_node": state.current_node,
            "execution_trace": trace
        }
        
        # Initialize default execution properties if missing
        if not state.request_id:
            updates["request_id"] = str(uuid.uuid4())
        if not state.session_id:
            updates["session_id"] = str(uuid.uuid4())
            
        # Log system status initialize
        meta = dict(state.metadata or {})
        meta["initialized_at"] = time.time()
        updates["metadata"] = meta
        
        return updates


class RouterAgentNode:
    """Executes Router Agent to classify user query intent and choose target agent"""

    async def __call__(self, state: GraphState) -> Dict[str, Any]:
        from app.core.dependencies import get_router_agent
        router_agent = get_router_agent()
        
        # Execute routing classification
        decision = await router_agent.run_routing(state.query or "")
        
        trace = list(state.execution_trace) if state.execution_trace else []
        trace.append(ROUTER_AGENT_NODE)
        
        meta = dict(state.metadata or {})
        meta["routing_confidence"] = decision.confidence
        meta["matched_rules"] = decision.matched_rules
        
        return {
            "current_node": ROUTER_AGENT_NODE,
            "previous_node": state.current_node,
            "detected_intent": decision.detected_intent,
            "selected_agent": decision.selected_agent,
            "execution_trace": trace,
            "metadata": meta
        }


class FinishNode:
    """Terminal node wrapping up execution status, compiling latencies and finalizing responses"""

    async def __call__(self, state: GraphState) -> Dict[str, Any]:
        trace = list(state.execution_trace) if state.execution_trace else []
        trace.append(FINISH_NODE)
        
        updates: Dict[str, Any] = {
            "current_node": FINISH_NODE,
            "previous_node": state.current_node,
            "execution_trace": trace
        }
        
        # Calculate execution latency if start time is logged in metadata
        init_time = (state.metadata or {}).get("initialized_at")
        if init_time:
            latency = (time.time() - init_time) * 1000.0
            updates["execution_time"] = latency
            
        # Default mock completion response if none is set
        if not state.response:
            updates["response"] = "Mock execution completed successfully via graph infrastructure nodes."
            
        return updates
