"""
Nura - Unit tests for BaseAgent framework
"""

import pytest
import asyncio
from typing import Any, Optional
from unittest.mock import MagicMock

from app.core.ai_config import AISettings
from app.utils.ai import agent_metrics
from app.agents import (
    BaseAgent,
    AgentContext,
    AgentResponse,
    AgentValidationError,
    AgentTimeoutError,
    AgentExecutionError
)


@pytest.fixture(autouse=True)
def reset_metrics():
    agent_metrics.reset()
    yield
    agent_metrics.reset()


@pytest.fixture
def mock_settings():
    return AISettings(
        GROQ_API_KEY="test_key",
        GROQ_MODEL="llama-3.3-70b-versatile",
        TIMEOUT_SECONDS=0.1,
        MAX_RETRIES=2,
        RETRY_MIN_DELAY=0.01,
        RETRY_MAX_DELAY=0.02
    )


class DummyAgent(BaseAgent):
    """Concrete dummy agent for lifecycle and validation testing"""
    
    def __init__(self, name="Dummy Agent", settings=None):
        super().__init__(name=name, settings=settings)
        self.lifecycle_steps = []

    def validate(self, input_data: Any, context: Optional[AgentContext] = None) -> None:
        super().validate(input_data, context)
        self.lifecycle_steps.append("validate")
        if isinstance(input_data, dict) and "invalid_key" in input_data:
            raise AgentValidationError("Key invalid_key is unsupported")

    def before_execute(self, input_data: Any, context: Optional[AgentContext] = None) -> None:
        super().before_execute(input_data, context)
        self.lifecycle_steps.append("before_execute")

    async def execute(self, input_data: Any, context: Optional[AgentContext] = None) -> Any:
        self.lifecycle_steps.append("execute")
        return {
            "response": f"processed: {input_data}",
            "citations": ["citation-1"],
            "metadata": {"test": True}
        }

    def after_execute(self, response: AgentResponse, context: Optional[AgentContext] = None) -> AgentResponse:
        self.lifecycle_steps.append("after_execute")
        response.metadata["after_processed"] = True
        return response


@pytest.mark.asyncio
async def test_agent_lifecycle_success(mock_settings):
    """Verify that all lifecycle hooks are executed in correct order on success"""
    agent = DummyAgent(settings=mock_settings)
    ctx = AgentContext(user_id="user-123", session_id="sess-456")
    
    response = await agent.run("hello payload", ctx)
    
    assert response.success is True
    assert response.agent_name == "Dummy Agent"
    assert response.response == "processed: hello payload"
    assert response.citations == ["citation-1"]
    assert response.metadata["test"] is True
    assert response.metadata["after_processed"] is True
    assert response.execution_time > 0.0
    
    # Check execution sequence of hooks
    assert agent.lifecycle_steps == ["validate", "before_execute", "execute", "after_execute"]
    
    # Verify metrics update
    metrics = agent_metrics.get_metrics()
    assert metrics["executions"] == 1
    assert metrics["failures"] == 0
    assert metrics["retries"] == 0


@pytest.mark.asyncio
async def test_agent_validation_empty_inputs(mock_settings):
    """Verify validation layer guards against empty/blank payloads"""
    agent = DummyAgent(settings=mock_settings)
    
    # 1. Test None payload
    response1 = await agent.run(None)
    assert response1.success is False
    assert "cannot be empty" in response1.message
    
    # 2. Test empty string payload
    response2 = await agent.run("   ")
    assert response2.success is False
    assert "cannot be empty" in response2.message

    # 3. Test custom validation logic
    response3 = await agent.run({"invalid_key": "val"})
    assert response3.success is False
    assert "invalid_key is unsupported" in response3.message
    
    # All are tracked as failures
    metrics = agent_metrics.get_metrics()
    assert metrics["executions"] == 3
    assert metrics["failures"] == 3


class RetryFailingAgent(BaseAgent):
    """Agent that fails a configurable number of times to verify retries and exponential backoff"""
    
    def __init__(self, failure_count: int, name="Retry Failing Agent", settings=None):
        super().__init__(name=name, settings=settings)
        self.failure_count = failure_count
        self.attempts = 0

    async def execute(self, input_data: Any, context: Optional[AgentContext] = None) -> Any:
        self.attempts += 1
        if self.attempts <= self.failure_count:
            raise ValueError(f"Simulated execution error attempt {self.attempts}")
        return "success after retries"


@pytest.mark.asyncio
async def test_agent_retry_handling_success(mock_settings):
    """Verify retries succeed if failures occur within max retry limit"""
    # MAX_RETRIES=2 -> execution is run 3 times total (1 initial + 2 retries)
    # Failure count = 2 -> attempts 1 and 2 fail, attempt 3 succeeds.
    agent = RetryFailingAgent(failure_count=2, settings=mock_settings)
    
    response = await agent.run("retry test")
    
    assert response.success is True
    assert response.response == "success after retries"
    assert agent.attempts == 3  # Initial + 2 retries
    
    metrics = agent_metrics.get_metrics()
    assert metrics["executions"] == 1
    assert metrics["failures"] == 0
    assert metrics["retries"] == 2


@pytest.mark.asyncio
async def test_agent_retry_handling_failure(mock_settings):
    """Verify retries fail and raise final AgentExecutionError when max retries are exceeded"""
    # Failure count = 3 -> attempt 1, 2, 3 fail. Run fails since max retries is 2.
    agent = RetryFailingAgent(failure_count=3, settings=mock_settings)
    
    response = await agent.run("retry test failing")
    
    assert response.success is False
    assert "Agent execution failed after 2 retries" in response.message
    assert agent.attempts == 3  # Initial + 2 retries
    
    metrics = agent_metrics.get_metrics()
    assert metrics["executions"] == 1
    assert metrics["failures"] == 1
    assert metrics["retries"] == 2


class TimeoutAgent(BaseAgent):
    """Agent that sleeps to simulate latency and trigger timeouts"""
    
    async def execute(self, input_data: Any, context: Optional[AgentContext] = None) -> Any:
        await asyncio.sleep(0.5)
        return "late response"


@pytest.mark.asyncio
async def test_agent_timeout_handling(mock_settings):
    """Verify agent execution triggers timeout exceptions when execution time exceeds setting parameters"""
    # TIMEOUT_SECONDS=0.1, execution sleeps for 0.5s -> should time out
    # MAX_RETRIES=2 -> will run 3 times total and fail.
    agent = TimeoutAgent(name="Timeout Agent", settings=mock_settings)
    
    response = await agent.run("timeout test")
    
    assert response.success is False
    assert "timed out after" in response.message
    
    metrics = agent_metrics.get_metrics()
    assert metrics["executions"] == 1
    assert metrics["failures"] == 1
    assert metrics["timeouts"] == 1
    assert metrics["retries"] == 2


@pytest.mark.asyncio
async def test_agent_context_propagation(mock_settings):
    """Verify AgentContext values propagate down to execute scope and telemetry logs"""
    class ContextAuditorAgent(BaseAgent):
        async def execute(self, input_data: Any, context: Optional[AgentContext] = None) -> Any:
            assert context is not None
            assert context.user_id == "auditor-user"
            assert context.patient_id == "auditor-patient"
            assert context.session_id == "auditor-session"
            assert context.metadata["custom_param"] == "custom_val"
            return "context verified"

    agent = ContextAuditorAgent(name="Context Auditor Agent", settings=mock_settings)
    ctx = AgentContext(
        user_id="auditor-user",
        patient_id="auditor-patient",
        session_id="auditor-session",
        metadata={"custom_param": "custom_val"}
    )
    
    response = await agent.run("run payload", ctx)
    assert response.success is True
    assert response.response == "context verified"


@pytest.mark.asyncio
async def test_agent_streaming_abstraction(mock_settings):
    """Verify streaming interfaces exist and yield the full response by default"""
    agent = DummyAgent(settings=mock_settings)
    ctx = AgentContext(user_id="stream-user")
    
    chunks = []
    async for chunk in agent.astream("streaming payload", ctx):
        assert isinstance(chunk, AgentResponse)
        chunks.append(chunk)
        
    assert len(chunks) == 1
    assert chunks[0].success is True
    assert chunks[0].response == "processed: streaming payload"
