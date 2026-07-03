"""
Nura - Background Tasks Manager
Executes non-blocking chat tasks asynchronously without delaying responses.
"""
import asyncio
import logging
from typing import Coroutine, Any, Set

logger = logging.getLogger("nura.chat.background")


class BackgroundTaskManager:
    """Manages asynchronous fire-and-forget execution of non-blocking tasks"""

    def __init__(self):
        self.active_tasks: Set[asyncio.Task] = set()

    def run_task(self, name: str, coro: Coroutine[Any, Any, Any]) -> None:
        """Schedules a coroutine to run concurrently, handling errors gracefully"""
        task = asyncio.create_task(coro, name=name)
        self.active_tasks.add(task)
        task.add_done_callback(lambda t: self._on_task_complete(name, t))

    def _on_task_complete(self, name: str, task: asyncio.Task) -> None:
        self.active_tasks.discard(task)
        try:
            task.result()
            logger.info(f"Background task '{name}' completed successfully.")
        except asyncio.CancelledError:
            logger.info(f"Background task '{name}' was cancelled.")
        except Exception as e:
            logger.error(f"Error in background task '{name}': {e}", exc_info=True)


# Global singleton instance
_background_task_manager_instance = BackgroundTaskManager()


def get_background_task_manager() -> BackgroundTaskManager:
    """Get the global BackgroundTaskManager singleton"""
    return _background_task_manager_instance
