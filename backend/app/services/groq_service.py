"""
Nura - Groq Service
Service wrapper for managing requests directly with Groq API
"""

import logging
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
        self.settings.validate_config()
        
        # Initialize client with timeout and max retries from config
        self.client = AsyncGroq(
            api_key=self.settings.GROQ_API_KEY,
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
        """Generate response for a prompt"""
        target_model = model or self.settings.GROQ_MODEL
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with handle_groq_exceptions():
            response = await self.client.chat.completions.create(
                model=target_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response

    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Any:
        """Generate JSON response for a prompt (enforces json_object format)"""
        target_model = model or self.settings.GROQ_MODEL
        # Enforce JSON formatting instructions in system prompt
        sys_prompt = system_prompt or "You are a helpful assistant. You must respond with a valid JSON object."
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": prompt}
        ]

        async with handle_groq_exceptions():
            response = await self.client.chat.completions.create(
                model=target_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
                **kwargs
            )
            return response

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
