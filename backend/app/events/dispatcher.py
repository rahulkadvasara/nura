"""
Nura - Event Dispatcher
Coordinates observer registration and event publication/dispatching
"""

import logging
import asyncio
from typing import Dict, List, Callable, Any
from app.events.base import BaseEvent

logger = logging.getLogger("nura.events.dispatcher")


class EventDispatcher:
    """Thread-safe event dispatcher coordinating publisher-subscriber mechanics"""

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}

    def register_handler(self, event_type: str, handler: Callable) -> None:
        """Subscribe a callback handler to a specific event type/topic"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        handler_name = getattr(handler, "__name__", str(handler))
        logger.info(f"Registered event handler '{handler_name}' for topic '{event_type}'")

    async def dispatch(self, event: BaseEvent) -> None:
        """Publish/dispatch an event instance, executing all registered handlers asynchronously"""
        event_type = event.event_type
        logger.info(f"Dispatching event '{event_type}' (id={event.event_id})")

        # Specific event handlers
        handlers = list(self._handlers.get(event_type, []))
        # Wildcard event handlers
        handlers.extend(self._handlers.get("*", []))

        if not handlers:
            logger.debug(f"No handlers registered for event topic '{event_type}'")
            return

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    # Run synchronous handler in a separate thread to prevent blocking event loop
                    await asyncio.to_thread(handler, event)
            except Exception as e:
                handler_name = getattr(handler, "__name__", str(handler))
                logger.error(
                    f"Execution failed for event handler '{handler_name}' on topic '{event_type}': {str(e)}",
                    exc_info=True
                )
