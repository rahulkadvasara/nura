"""
Nura - Base Agent
"""
import time
import asyncio
from abc import ABC, abstractmethod
from typing import Any, Optional, AsyncGenerator

from app.core.logging import get_logger
from app.core.ai_config import ai_settings
from app.utils.ai import agent_metrics
from app.agents.base.context import AgentContext
from app.agents.base.response import AgentResponse
from app.agents.base.exceptions import (
    AgentValidationError,
    AgentExecutionError,
    AgentTimeoutError
)

class BaseAgent(ABC):
    """Abstract base class for all platform AI agents"""

    def __init__(self, name: str, settings=ai_settings):
        self.name = name
        self.settings = settings
        self.logger = get_logger(f"nura.agents.{name.lower().replace(' ', '_')}")

    def validate(self, input_data: Any, context: Optional[AgentContext] = None) -> None:
        """Validate input payload and context. Raises AgentValidationError if invalid."""
        if input_data is None:
            raise AgentValidationError("Execution input payload cannot be empty")
        if isinstance(input_data, str) and not input_data.strip():
            raise AgentValidationError("Execution input string cannot be empty")

    def before_execute(self, input_data: Any, context: Optional[AgentContext] = None) -> None:
        """Lifecycle hook executed before calling the primary execute block"""
        pass

    @abstractmethod
    async def execute(self, input_data: Any, context: Optional[AgentContext] = None) -> Any:
        """Core execution block. Inherited agents must implement this method."""
        pass

    def after_execute(self, response: AgentResponse, context: Optional[AgentContext] = None) -> AgentResponse:
        """Lifecycle hook executed after execute completes, before returning response"""
        return response

    def handle_error(self, error: Exception, context: Optional[AgentContext] = None) -> AgentResponse:
        """Error handler hook to map internal exceptions to standard AgentResponse schema"""
        self.logger.error(
            f"Agent {self.name} encountered error: {str(error)}",
            exc_info=True,
            extra={
                "agent_name": self.name,
                "user_id": context.user_id if context else None,
                "session_id": context.session_id if context else None,
                "status": "error"
            }
        )
        return AgentResponse(
            success=False,
            message=str(error),
            response=None,
            citations=[],
            metadata={},
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            execution_time=0.0,
            agent_name=self.name
        )

    async def run(self, input_data: Any, context: Optional[AgentContext] = None) -> AgentResponse:
        """Runs the lifecycle of the agent, executing the core agent task with retries, timeout, and validation"""
        ctx = context or AgentContext()
        start_time = time.perf_counter()
        
        # Standardized logging on execution start
        self.logger.info(
            f"Agent {self.name} starting execution",
            extra={
                "agent_name": self.name,
                "user_id": ctx.user_id,
                "session_id": ctx.session_id,
                "request_id": ctx.request_id,
                "status": "started"
            }
        )

        retry_count = 0
        max_retries = self.settings.MAX_RETRIES
        delay = self.settings.RETRY_MIN_DELAY
        timeout_seconds = self.settings.TIMEOUT_SECONDS
        
        # Telemetry metrics collection parameters
        success = False
        timeout_occurred = False
        result = None
        usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        citations = []
        metadata = {}

        try:
            # 1. Validation
            self.validate(input_data, ctx)
            
            # 2. Before Execute Hook
            self.before_execute(input_data, ctx)

            # 3. Execution wrapper with timeout and retry loops
            while True:
                try:
                    # Execute async with timeout wrapping
                    async with asyncio.timeout(timeout_seconds):
                        result = await self.execute(input_data, ctx)
                    success = True
                    break
                except asyncio.TimeoutError as e:
                    timeout_occurred = True
                    self.logger.warning(
                        f"Agent {self.name} timed out after {timeout_seconds} seconds (retry {retry_count}/{max_retries})",
                        extra={
                            "agent_name": self.name,
                            "user_id": ctx.user_id,
                            "session_id": ctx.session_id,
                            "retry_count": retry_count
                        }
                    )
                    if retry_count >= max_retries:
                        raise AgentTimeoutError(f"Agent execution timed out after {timeout_seconds}s and {max_retries} retries") from e
                except Exception as e:
                    self.logger.warning(
                        f"Agent {self.name} encountered error during execution (retry {retry_count}/{max_retries}): {str(e)}",
                        extra={
                            "agent_name": self.name,
                            "user_id": ctx.user_id,
                            "session_id": ctx.session_id,
                            "retry_count": retry_count
                        }
                    )
                    if retry_count >= max_retries:
                        if isinstance(e, AgentValidationError):
                            raise e
                        raise AgentExecutionError(f"Agent execution failed after {max_retries} retries: {str(e)}") from e

                # Exponential backoff delay
                retry_count += 1
                await asyncio.sleep(delay)
                delay = min(delay * 2.0, self.settings.RETRY_MAX_DELAY)

            # Determine response output shape
            if isinstance(result, AgentResponse):
                response_obj = result
            else:
                msg = "Execution completed successfully"
                resp_val = result
                if isinstance(result, dict):
                    msg = result.get("message", msg)
                    resp_val = result.get("response", result)
                    usage = result.get("usage", usage)
                    citations = result.get("citations", citations)
                    metadata = result.get("metadata", metadata)

                latency_ms = (time.perf_counter() - start_time) * 1000.0
                response_obj = AgentResponse(
                    success=True,
                    message=msg,
                    response=resp_val,
                    citations=citations,
                    metadata=metadata,
                    usage=usage,
                    execution_time=latency_ms,
                    agent_name=self.name
                )

            # 4. After Execute Hook
            response_obj = self.after_execute(response_obj, ctx)
            
            # Record success metrics
            tokens_used = response_obj.usage.get("total_tokens", 0)
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            response_obj.execution_time = latency_ms

            agent_metrics.record_execution(
                latency_ms=latency_ms,
                success=True,
                tokens=tokens_used,
                retries=retry_count,
                timeout=False,
                model=ctx.metadata.get("model") or self.settings.GROQ_MODEL
            )

            self.logger.info(
                f"Agent {self.name} completed execution successfully",
                extra={
                    "agent_name": self.name,
                    "user_id": ctx.user_id,
                    "session_id": ctx.session_id,
                    "request_id": ctx.request_id,
                    "execution_time_ms": latency_ms,
                    "retry_count": retry_count,
                    "status": "success"
                }
            )

            return response_obj

        except Exception as err:
            # 5. Handle Error Hook
            response_obj = self.handle_error(err, ctx)
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            response_obj.execution_time = latency_ms
            
            agent_metrics.record_execution(
                latency_ms=latency_ms,
                success=False,
                tokens=0,
                retries=retry_count,
                timeout=timeout_occurred,
                model=ctx.metadata.get("model") or self.settings.GROQ_MODEL
            )

            self.logger.error(
                f"Agent {self.name} failed execution",
                extra={
                    "agent_name": self.name,
                    "user_id": ctx.user_id,
                    "session_id": ctx.session_id,
                    "request_id": ctx.request_id,
                    "execution_time_ms": latency_ms,
                    "retry_count": retry_count,
                    "status": "failed"
                }
            )
            return response_obj

    def stream(self, input_data: Any, context: Optional[AgentContext] = None) -> Any:
        """Stream interface. Raises NotImplementedError for synchronous stream calls."""
        raise NotImplementedError("Sync streaming is not supported. Use astream instead.")

    async def astream(self, input_data: Any, context: Optional[AgentContext] = None) -> AsyncGenerator[AgentResponse, None]:
        """Asynchronously stream chunks of response. Defaults to yielding standard response payload in one chunk."""
        response = await self.run(input_data, context)
        yield response
