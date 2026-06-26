"""
Nura - Unit tests for EventDispatcher
"""

import pytest
import asyncio
from unittest.mock import MagicMock

from app.events.base import BaseEvent
from app.events.dispatcher import EventDispatcher


class DummyEvent(BaseEvent):
    """Simple test event"""
    def __init__(self, key: str, **kwargs):
        super().__init__(event_type="DummyEvent", payload={"key": key, **kwargs})


@pytest.mark.asyncio
async def test_dispatcher_sync_and_async_handlers():
    """Verify that synchronous and asynchronous handlers are executed on dispatch"""
    dispatcher = EventDispatcher()
    
    sync_called = False
    async_called = False

    def sync_handler(event: BaseEvent):
        nonlocal sync_called
        sync_called = True
        assert event.payload["key"] == "val1"

    async def async_handler(event: BaseEvent):
        nonlocal async_called
        async_called = True
        assert event.payload["key"] == "val1"

    dispatcher.register_handler("DummyEvent", sync_handler)
    dispatcher.register_handler("DummyEvent", async_handler)

    test_event = DummyEvent(key="val1")
    await dispatcher.dispatch(test_event)

    assert sync_called is True
    assert async_called is True


@pytest.mark.asyncio
async def test_dispatcher_wildcard_handlers():
    """Verify wildcard handlers receive all dispatched events"""
    dispatcher = EventDispatcher()
    
    wildcard_called_count = 0

    async def wildcard_handler(event: BaseEvent):
        nonlocal wildcard_called_count
        wildcard_called_count += 1

    dispatcher.register_handler("*", wildcard_handler)

    # Dispatch multiple different events
    await dispatcher.dispatch(DummyEvent(key="first"))
    
    class AnotherDummyEvent(BaseEvent):
        def __init__(self):
            super().__init__(event_type="AnotherEvent", payload={})

    await dispatcher.dispatch(AnotherDummyEvent())

    assert wildcard_called_count == 2


@pytest.mark.asyncio
async def test_dispatcher_handler_exceptions():
    """Verify that exceptions in handlers do not block other handlers or propagate to the publisher"""
    dispatcher = EventDispatcher()

    sync_called = False
    async_called = False

    def sync_broken_handler(event: BaseEvent):
        raise ValueError("Broken sync handler error")

    def sync_handler(event: BaseEvent):
        nonlocal sync_called
        sync_called = True

    async def async_broken_handler(event: BaseEvent):
        raise RuntimeError("Broken async handler error")

    async def async_handler(event: BaseEvent):
        nonlocal async_called
        async_called = True

    dispatcher.register_handler("DummyEvent", sync_broken_handler)
    dispatcher.register_handler("DummyEvent", sync_handler)
    dispatcher.register_handler("DummyEvent", async_broken_handler)
    dispatcher.register_handler("DummyEvent", async_handler)

    test_event = DummyEvent(key="error_test")
    
    # Should not raise any error to the caller
    await dispatcher.dispatch(test_event)

    assert sync_called is True
    assert async_called is True
