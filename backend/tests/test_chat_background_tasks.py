import asyncio
import pytest
from app.services.chat.background_tasks import BackgroundTaskManager


@pytest.mark.asyncio
async def test_background_task_success():
    manager = BackgroundTaskManager()
    completed = False

    async def sample_coro():
        nonlocal completed
        await asyncio.sleep(0.1)
        completed = True

    manager.run_task("test-success", sample_coro())
    
    # Assert it started running and is tracked
    assert len(manager.active_tasks) == 1
    
    # Wait for completion
    await asyncio.sleep(0.2)
    assert completed is True
    assert len(manager.active_tasks) == 0


@pytest.mark.asyncio
async def test_background_task_exception_graceful():
    manager = BackgroundTaskManager()

    async def failing_coro():
        await asyncio.sleep(0.1)
        raise RuntimeError("Something failed in background")

    # This should log the error but not raise/crash the event loop
    manager.run_task("test-failure", failing_coro())
    
    await asyncio.sleep(0.2)
    assert len(manager.active_tasks) == 0
