"""
Pytest configuration for the Nura backend test suite.
Sets asyncio_mode to "auto" so every async test function is treated as an
asyncio coroutine without needing the @pytest.mark.asyncio decorator.
"""

import pytest
import httpx

# Monkeypatch httpx.Client to work around starlette testclient compatibility issues
original_init = httpx.Client.__init__
def patched_init(self, *args, **kwargs):
    kwargs.pop("app", None)
    original_init(self, *args, **kwargs)
httpx.Client.__init__ = patched_init



# Make every async test auto-wrapped by pytest-asyncio
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "asyncio: mark test as an asyncio coroutine"
    )
