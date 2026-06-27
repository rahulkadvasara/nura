"""
Nura - LangGraph API Schemas
Pydantic validation response and request models for administrative graph routing endpoints.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class GraphHealthResponse(BaseModel):
    """Schema representing compilation and runtime status of the state graph"""
    graph_compiled: bool = Field(..., description="Indicates if the graph builder completed compilation successfully")
    graph_version: str = Field(..., description="Current version string of the active graph framework settings")
    registered_nodes: List[str] = Field(..., description="List of names of all registered nodes")
    registered_transitions: List[Dict[str, Any]] = Field(..., description="List of configured normal/conditional node transitions")
    active_executions: int = Field(..., description="Count of currently active pipeline executions running")


class GraphNodesResponse(BaseModel):
    """Response containing registered nodes list"""
    nodes: List[str] = Field(..., description="Names of all registered workflow nodes")


class GraphTestRunRequest(BaseModel):
    """Request query options to execute a placeholder mock graph execution trace test"""
    query: Optional[str] = Field(default=None, description="Optional raw query string text to process")
    patient_id: Optional[str] = Field(default=None, description="Optional target patient profile ID context")
    debug_mode: bool = Field(default=False, description="Flag indicating cache-bypass debug trace mode")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional custom metadata payload variables")


class GraphTestRunResponse(BaseModel):
    """Response trace results containing execution timelines and serialized output state"""
    trace: List[str] = Field(..., description="Order log list of nodes traversed in sequence")
    timings: Dict[str, float] = Field(..., description="Execution duration timing metrics per node and overall run in milliseconds")
    execution_metadata: Dict[str, Any] = Field(..., description="Underlying session meta flags recorded")
    state: Dict[str, Any] = Field(..., description="Final serialized state dictionary output payload")


class GraphStatisticsResponse(BaseModel):
    """Telemetry performance statistics deck for monitoring graph runs"""
    total_executions: int = Field(..., description="Aggregated count of all graph executions launched")
    successful_executions: int = Field(..., description="Count of runs completing with success status")
    failed_executions: int = Field(..., description="Count of runs encountering exceptions/failures")
    avg_latency: float = Field(..., description="Average latency duration of successful runs in milliseconds")
    timeout_count: int = Field(..., description="Number of execution runs timed out")
    cancelled_count: int = Field(..., description="Number of execution runs cancelled by task management")
    active_executions: int = Field(..., description="Count of currently active running execution routines")
    graph_version: str = Field(..., description="Active version of the execution graph schema")
    node_execution_count: Dict[str, int] = Field(..., description="Map logging invocation frequency per node ID")
    transition_count: Dict[str, int] = Field(..., description="Map logging traversal counts of transition links")
