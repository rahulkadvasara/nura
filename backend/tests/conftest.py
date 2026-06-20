"""
Pytest configuration for the Nura backend test suite.
Sets asyncio_mode to "auto" so every async test function is treated as an
asyncio coroutine without needing the @pytest.mark.asyncio decorator.
"""

import pytest


# Make every async test auto-wrapped by pytest-asyncio
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "asyncio: mark test as an asyncio coroutine"
    )
