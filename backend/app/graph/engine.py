"""
Nura - LangGraph Execution Engine
Runs stateful workflows with timeouts, retry logic, cancellation controls, and telemetry hooks.
"""

import time
import asyncio
import logging
from typing import Dict, Any, AsyncGenerator, Optional
from app.core.ai_config import ai_settings
from app.graph.registry import NodeRegistry
from app.graph.transitions import TransitionManager
from app.graph.state import GraphState
from app.graph.constants import START_NODE, INIT_STATE_NODE, ROUTER_AGENT_NODE, FINISH_NODE
from app.graph.telemetry import GraphTelemetryTracker, get_graph_telemetry

logger = logging.getLogger("nura.graph.engine")


class LangGraphEngine:
    """Stateful directed graph workflow execution runner"""

    def __init__(
        self,
        registry: NodeRegistry,
        transitions: TransitionManager,
        telemetry: Optional[GraphTelemetryTracker] = None
    ):
        self.registry = registry
        self.transitions = transitions
        self.telemetry = telemetry or get_graph_telemetry()

    def execute(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronously execute the graph workflow wrapper"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.execute_async(state_dict))

    async def execute_async(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Asynchronously execute the graph workflow.
        Applies timeout, retry policy, cancellation safeguards, and tracing logs.
        """
        self.telemetry.record_start()
        start_time = time.time()
        
        state = GraphState.from_dict(state_dict)
        state.current_node = START_NODE
        state.previous_node = None
        state.execution_trace = []
        state.error = None
        
        curr_node_name = START_NODE
        
        try:
            # Apply overall execution timeout limit
            async with asyncio.timeout(ai_settings.GRAPH_TIMEOUT):
                while curr_node_name:
                    # Check for asyncio task cancellation flag
                    if asyncio.current_task() and asyncio.current_task().cancelled():
                        raise asyncio.CancelledError("Graph execution task was cancelled.")
                    
                    node_callable = self.registry.lookup_node(curr_node_name)
                    self.telemetry.record_node_execution(curr_node_name)
                    
                    # Execute node callback with retries config
                    updates = await self._execute_node_with_retry(curr_node_name, node_callable, state)
                    
                    # Merge updates into state object
                    state = state.model_copy(update=updates)
                    
                    # Resolve next node in loop
                    next_node_name = self.transitions.get_next_node(curr_node_name, state)
                    
                    if next_node_name:
                        self.telemetry.record_transition(curr_node_name, next_node_name)
                        
                    state.previous_node = curr_node_name
                    state.current_node = next_node_name
                    
                    if curr_node_name == FINISH_NODE or not next_node_name:
                        break
                        
                    curr_node_name = next_node_name
                    
            latency_ms = (time.time() - start_time) * 1000.0
            state.execution_time = latency_ms
            self.telemetry.record_success(latency_ms)
            logger.info(f"Graph execution finished successfully in {latency_ms:.2f}ms.")
            return state.to_dict()

        except TimeoutError as te:
            error_msg = f"Graph execution timed out after {ai_settings.GRAPH_TIMEOUT} seconds."
            logger.error(error_msg)
            state.error = error_msg
            self.telemetry.record_failure(timeout=True)
            return state.to_dict()
            
        except asyncio.CancelledError as ce:
            error_msg = "Graph execution cancelled by caller task."
            logger.error(error_msg)
            state.error = error_msg
            self.telemetry.record_failure(cancelled=True)
            return state.to_dict()
            
        except Exception as e:
            error_msg = f"Graph execution failed: {str(e)}"
            logger.exception(error_msg)
            state.error = error_msg
            self.telemetry.record_failure()
            return state.to_dict()

    async def stream(self, state_dict: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute graph and yield state update events at node boundaries.
        Allows real-time streaming updates from the UI.
        """
        self.telemetry.record_start()
        start_time = time.time()
        
        state = GraphState.from_dict(state_dict)
        state.current_node = START_NODE
        state.previous_node = None
        state.execution_trace = []
        state.error = None
        
        curr_node_name = START_NODE
        
        try:
            async with asyncio.timeout(ai_settings.GRAPH_TIMEOUT):
                while curr_node_name:
                    if asyncio.current_task() and asyncio.current_task().cancelled():
                        raise asyncio.CancelledError()
                    
                    node_callable = self.registry.lookup_node(curr_node_name)
                    self.telemetry.record_node_execution(curr_node_name)
                    
                    updates = await self._execute_node_with_retry(curr_node_name, node_callable, state)
                    state = state.model_copy(update=updates)
                    
                    # Yield current step update state to the stream generator
                    yield state.to_dict()
                    
                    next_node_name = self.transitions.get_next_node(curr_node_name, state)
                    if next_node_name:
                        self.telemetry.record_transition(curr_node_name, next_node_name)
                        
                    state.previous_node = curr_node_name
                    state.current_node = next_node_name
                    
                    if curr_node_name == FINISH_NODE or not next_node_name:
                        break
                        
                    curr_node_name = next_node_name
                    
            latency_ms = (time.time() - start_time) * 1000.0
            self.telemetry.record_success(latency_ms)

        except TimeoutError:
            state.error = f"Graph execution timed out after {ai_settings.GRAPH_TIMEOUT} seconds."
            self.telemetry.record_failure(timeout=True)
            yield state.to_dict()
            
        except asyncio.CancelledError:
            state.error = "Graph execution cancelled."
            self.telemetry.record_failure(cancelled=True)
            yield state.to_dict()
            
        except Exception as e:
            state.error = f"Graph execution failed: {str(e)}"
            self.telemetry.record_failure()
            yield state.to_dict()

    async def _execute_node_with_retry(
        self,
        node_name: str,
        node_callable: Any,
        state: GraphState
    ) -> Dict[str, Any]:
        """Execute node callable wrapping retry backoff controls"""
        retries = ai_settings.GRAPH_MAX_RETRIES
        delay = 0.5  # initial retry delay
        
        for attempt in range(retries + 1):
            try:
                # Call node async
                return await node_callable(state)
            except Exception as e:
                if attempt == retries:
                    logger.error(f"Node '{node_name}' execution failed after max retries: {str(e)}")
                    raise e
                logger.warning(f"Node '{node_name}' failed (attempt {attempt + 1}/{retries + 1}). Retrying in {delay}s...")
                await asyncio.sleep(delay)
                delay *= 2.0  # exponential backoff


# Global engine singleton lazy-initialized via builder compiler
_engine_instance: Optional[LangGraphEngine] = None


def get_graph_engine() -> LangGraphEngine:
    """Retrieve compiled singleton instance of LangGraphEngine"""
    global _engine_instance
    if _engine_instance is None:
        from app.graph.builder import get_graph_builder
        builder = get_graph_builder()
        
        # Proactively load/bootstrap default infrastructure nodes and transitions
        from app.graph.nodes import StartNode, InitializeStateNode, RouterAgentNode, FinishNode
        
        # Register standard nodes to builder registry if not already present
        registered_nodes = builder.registry.list_nodes()
        if START_NODE not in registered_nodes:
            builder.add_node(START_NODE, StartNode())
        if INIT_STATE_NODE not in registered_nodes:
            builder.add_node(INIT_STATE_NODE, InitializeStateNode())
        if ROUTER_AGENT_NODE not in registered_nodes:
            builder.add_node(ROUTER_AGENT_NODE, RouterAgentNode())
        if FINISH_NODE not in registered_nodes:
            builder.add_node(FINISH_NODE, FinishNode())
            
        # Core Knowledge Agent nodes registration
        if "MedicalKnowledgeAgent" not in registered_nodes:
            from app.graph.nodes import MedicalKnowledgeAgentNode
            builder.add_node("MedicalKnowledgeAgent", MedicalKnowledgeAgentNode())
        if "SymptomAgent" not in registered_nodes:
            from app.graph.nodes import SymptomAgentNode
            builder.add_node("SymptomAgent", SymptomAgentNode())
        if "MemoryAgent" not in registered_nodes:
            from app.graph.nodes import MemoryAgentNode
            builder.add_node("MemoryAgent", MemoryAgentNode())
        if "UnknownAgent" not in registered_nodes:
            from app.graph.nodes import UnknownAgentNode
            builder.add_node("UnknownAgent", UnknownAgentNode())
        
        # Reset transition list to avoid duplicate paths stacking
        builder.transitions.clear()
        builder.add_transition(START_NODE, INIT_STATE_NODE)
        builder.add_transition(INIT_STATE_NODE, ROUTER_AGENT_NODE)
        
        # Dynamic dispatch transition from Router based on state.selected_agent
        builder.add_conditional_transition(
            source=ROUTER_AGENT_NODE,
            condition_func=lambda state: state.selected_agent or "UnknownAgent",
            mapping={
                "MedicalKnowledgeAgent": "MedicalKnowledgeAgent",
                "SymptomAgent": "SymptomAgent",
                "MemoryAgent": "MemoryAgent",
                "UnknownAgent": "UnknownAgent"
            }
        )
        
        # Finalize execution transitions from agent executors to Finish node
        builder.add_transition("MedicalKnowledgeAgent", FINISH_NODE)
        builder.add_transition("SymptomAgent", FINISH_NODE)
        builder.add_transition("MemoryAgent", FINISH_NODE)
        builder.add_transition("UnknownAgent", FINISH_NODE)
        
        # Compile engine
        _engine_instance = builder.compile()
        
    return _engine_instance
