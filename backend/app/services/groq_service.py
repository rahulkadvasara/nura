"""
Nura - Groq Service
Service wrapper for managing requests directly with Groq API
"""

import logging
import asyncio
from typing import Optional, Any, AsyncGenerator
from contextlib import asynccontextmanager
from groq import AsyncGroq
import groq

from app.core.ai_config import AISettings, ai_settings
from app.core.exceptions import (
    AIConfigurationError,
    AIConnectionError,
    AITimeoutError,
    AIRateLimitError,
    AIResponseError
)
from app.core.logging import get_logger

logger = get_logger("nura.ai.groq")


@asynccontextmanager
async def handle_groq_exceptions():
    """Context manager to map Groq exceptions to custom AI exceptions"""
    try:
        yield
    except groq.APITimeoutError as e:
        logger.error(f"Groq API timeout: {str(e)}")
        raise AITimeoutError(f"Groq API timeout occurred: {str(e)}") from e
    except groq.APIConnectionError as e:
        logger.error(f"Groq API connection error: {str(e)}")
        raise AIConnectionError(f"Groq API connection error: {str(e)}") from e
    except groq.RateLimitError as e:
        logger.warning(f"Groq API rate limit: {str(e)}")
        raise AIRateLimitError(f"Groq API rate limit reached: {str(e)}") from e
    except groq.APIStatusError as e:
        logger.error(f"Groq API status error {e.status_code}: {str(e)}")
        raise AIResponseError(f"Groq API status error: {str(e)}") from e
    except groq.APIError as e:
        logger.error(f"Groq API error: {str(e)}")
        raise AIResponseError(f"Groq API error: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error in Groq service: {str(e)}")
        raise AIResponseError(f"An unexpected error occurred in Groq service: {str(e)}") from e


class GroqService:
    """Service wrapper around AsyncGroq client"""
    
    def __init__(self, settings: AISettings = ai_settings):
        self.settings = settings
        # Validate configuration before initializing client
        try:
            self.settings.validate_config()
        except AIConfigurationError as e:
            logger.warning(f"Groq API Key configuration missing/unvalidated: {e}")

        # Initialize client with timeout and max retries from config
        api_key = self.settings.GROQ_API_KEY if (self.settings.GROQ_API_KEY and self.settings.GROQ_API_KEY.strip()) else "dummy_key_for_testing"
        self.client = AsyncGroq(
            api_key=api_key,
            timeout=self.settings.TIMEOUT_SECONDS,
            max_retries=self.settings.MAX_RETRIES
        )
        logger.info("GroqService initialized successfully")


    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Any:
        """Generate response for a prompt, protected by a circuit breaker"""
        target_model = model or self.settings.GROQ_MODEL
        # Truncate prompt to safe character payload size limits (3500 chars) to avoid 413 & rate limits
        safe_prompt = prompt[:3500] if len(prompt) > 3500 else prompt
        safe_sys = system_prompt[:2000] if system_prompt and len(system_prompt) > 2000 else system_prompt

        messages = []
        if safe_sys:
            messages.append({"role": "system", "content": safe_sys})
        messages.append({"role": "user", "content": safe_prompt})

        from app.utils.circuit_breaker import get_circuit_breaker
        
        def fallback_groq(*args, **fallback_kwargs):
            logger.error("Groq API circuit breaker fallback triggered.")
            class MockMessage:
                content = "Service temporarily unavailable due to upstream API issues. Fallback triggered."
                role = "assistant"
            class MockChoice:
                message = MockMessage()
                finish_reason = "stop"
            class MockUsage:
                prompt_tokens = 0
                completion_tokens = 0
                total_tokens = 0
            class MockResponse:
                id = "mock-id"
                choices = [MockChoice()]
                model = "fallback-model"
                usage = MockUsage()
            return MockResponse()

        cb = get_circuit_breaker("groq_service", fallback_func=fallback_groq)

        async def do_generate():
            if not self.settings.GROQ_API_KEY or "dummy_key" in self.settings.GROQ_API_KEY:
                logger.info("GROQ_API_KEY not configured or dummy key detected. Returning fallback response.")
                return fallback_groq()

            current_model = target_model

            for attempt in range(3):
                try:
                    async with handle_groq_exceptions():
                        response = await self.client.chat.completions.create(
                            model=current_model,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            **kwargs
                        )
                        return response
                except (AIRateLimitError, AIResponseError) as err:
                    backup = self.settings.GROQ_BACKUP_MODEL
                    if attempt == 0 and current_model != backup:
                        logger.warning(f"Groq exception ({err}) on {current_model}. Fallback switching to '{backup}'...")
                        current_model = backup
                    elif attempt < 2:
                        logger.warning(f"Groq exception ({err}) on {current_model}. Backoff sleeping 2.5s (attempt {attempt + 1}/3)...")
                        await asyncio.sleep(2.5)
                    else:
                        raise err

        return await cb.execute_async(do_generate)

    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Any:
        """Generate JSON response for a prompt (enforces json_object format), protected by a circuit breaker"""
        target_model = model or self.settings.GROQ_MODEL
        # Enforce JSON formatting instructions in system prompt
        sys_prompt = system_prompt or "You are a helpful assistant. You must respond with a valid JSON object."
        safe_prompt = prompt[:3500] if len(prompt) > 3500 else prompt
        safe_sys = sys_prompt[:2000] if len(sys_prompt) > 2000 else sys_prompt

        messages = [
            {"role": "system", "content": safe_sys},
            {"role": "user", "content": safe_prompt}
        ]

        from app.utils.circuit_breaker import get_circuit_breaker
        
        def fallback_groq_json(*args, **fallback_kwargs):
            logger.error("Groq API JSON circuit breaker fallback triggered.")
            class MockMessage:
                content = '{"error": "Service temporarily unavailable", "status": "degraded"}'
                role = "assistant"
            class MockChoice:
                message = MockMessage()
                finish_reason = "stop"
            class MockUsage:
                prompt_tokens = 0
                completion_tokens = 0
                total_tokens = 0
            class MockResponse:
                id = "mock-id"
                choices = [MockChoice()]
                model = "fallback-model"
                usage = MockUsage()
            return MockResponse()

        cb = get_circuit_breaker("groq_service_json", fallback_func=fallback_groq_json)

        async def do_generate_json():
            if not self.settings.GROQ_API_KEY or "dummy_key" in self.settings.GROQ_API_KEY:
                logger.info("GROQ_API_KEY not configured or dummy key detected. Returning fallback JSON response.")
                return fallback_groq_json()

            current_model = target_model

            for attempt in range(3):
                try:
                    async with handle_groq_exceptions():
                        response = await self.client.chat.completions.create(
                            model=current_model,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            response_format={"type": "json_object"},
                            **kwargs
                        )
                        return response
                except (AIRateLimitError, AIResponseError) as err:
                    backup = self.settings.GROQ_BACKUP_MODEL
                    if attempt == 0 and current_model != backup:
                        logger.warning(f"Groq exception ({err}) on {current_model}. Fallback switching to '{backup}'...")
                        current_model = backup
                    elif attempt < 2:
                        logger.warning(f"Groq exception ({err}) on {current_model}. Backoff sleeping 2.5s (attempt {attempt + 1}/3)...")
                        await asyncio.sleep(2.5)
                    else:
                        raise err

        return await cb.execute_async(do_generate_json)

    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[Any, None]:
        """Stream chat completion response"""
        target_model = model or self.settings.GROQ_MODEL
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with handle_groq_exceptions():
            response_stream = await self.client.chat.completions.create(
                model=target_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )
            async for chunk in response_stream:
                yield chunk

    async def health_check(self) -> dict:
        """Perform a check to confirm Groq API connectivity"""
        import time
        from datetime import datetime, timezone
        
        start_time = time.time()
        try:
            self.settings.validate_config()
            # Issue a tiny generation request as a ping
            await self.client.chat.completions.create(
                model=self.settings.GROQ_MODEL,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1
            )
            latency = (time.time() - start_time) * 1000.0
            return {
                "reachable": True,
                "model": self.settings.GROQ_MODEL,
                "latency_ms": latency,
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            latency = (time.time() - start_time) * 1000.0
            logger.error(f"Groq health check failed: {str(e)}")
            return {
                "reachable": False,
                "model": self.settings.GROQ_MODEL,
                "latency_ms": latency,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }


# Singleton reference cache
_groq_service_instance: Optional[GroqService] = None

def get_groq_service() -> GroqService:
    """Retrieve singleton instance of GroqService"""
    global _groq_service_instance
    if _groq_service_instance is None:
        _groq_service_instance = GroqService(settings=ai_settings)
    return _groq_service_instance
