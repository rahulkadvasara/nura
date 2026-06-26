"""
Nura - Event Queue
Handles background processing of events, retry mechanisms with exponential backoff, and DLQ database persistence
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.events.base import BaseEvent
from app.db import get_database
from app.utils.ai import memory_sync_metrics

logger = logging.getLogger("nura.events.queue")


class EventQueue:
    """Async background processing queue with exponential backoff retries and database DLQ"""

    def __init__(self, max_retries: int = 3, base_delay: float = 2.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self._queue = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False
        self._sync_service = None

    def set_sync_service(self, sync_service) -> None:
        """Inject MemorySyncService dependency"""
        self._sync_service = sync_service

    def start(self) -> None:
        """Start the background consumer worker task"""
        if self._running:
            return
        self._running = True
        self._worker_task = asyncio.create_task(self._worker_loop())
        logger.info("Background EventQueue worker started successfully")

    async def stop(self) -> None:
        """Stop the worker loop and wait for cancellation"""
        if not self._running:
            return
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("Background EventQueue worker stopped")

    def push(self, event: BaseEvent) -> None:
        """Enqueue an event for asynchronous processing"""
        self._queue.put_nowait((event, 0))  # Tuple: (Event, current_retry_count)
        logger.debug(f"Event enqueued: {event.event_type} (id={event.event_id}, queue_size={self.qsize()})")

    def qsize(self) -> int:
        """Return current size of the async queue"""
        return self._queue.qsize()

    async def get_dlq_jobs(self) -> List[Dict[str, Any]]:
        """Fetch all failed synchronization attempts from the Dead-Letter Queue (MongoDB)"""
        try:
            db = get_database()
            cursor = db.sync_dlq.find({})
            jobs = await cursor.to_list(length=100)
            for job in jobs:
                if "_id" in job:
                    job["id"] = str(job.pop("_id"))
            return jobs
        except Exception as e:
            logger.error(f"Failed to query DLQ jobs from MongoDB: {str(e)}")
            return []

    async def retry_dlq_job(self, event_id: str) -> bool:
        """Remove a specific job from DLQ database and re-enqueue it"""
        try:
            db = get_database()
            job = await db.sync_dlq.find_one({"event_id": event_id})
            if not job:
                logger.warning(f"No DLQ job found matching event_id '{event_id}'")
                return False

            # Convert database document back to BaseEvent structure
            event = BaseEvent(
                event_id=job["event_id"],
                event_type=job["event_type"],
                timestamp=datetime.fromisoformat(job["timestamp"]) if isinstance(job["timestamp"], str) else job["timestamp"],
                payload=job["payload"]
            )

            # Re-enqueue with retry counter reset to 0
            self._queue.put_nowait((event, 0))
            await db.sync_dlq.delete_one({"event_id": event_id})
            logger.info(f"Re-enqueued DLQ job {event_id} for retry processing")
            return True
        except Exception as e:
            logger.error(f"Failed to retry DLQ job {event_id}: {str(e)}")
            return False

    async def retry_all_dlq_jobs(self) -> int:
        """Retry and clear all jobs currently in the DLQ"""
        try:
            db = get_database()
            cursor = db.sync_dlq.find({})
            jobs = await cursor.to_list(length=1000)
            count = 0
            for job in jobs:
                event_id = job["event_id"]
                success = await self.retry_dlq_job(event_id)
                if success:
                    count += 1
            logger.info(f"Successfully re-enqueued {count} DLQ jobs for execution")
            return count
        except Exception as e:
            logger.error(f"Failed to retry all DLQ jobs: {str(e)}")
            return 0

    async def _push_to_dlq(self, event: BaseEvent, error_msg: str, retries: int) -> None:
        """Persist a failed event task into the sync_dlq MongoDB collection"""
        try:
            db = get_database()
            dlq_record = {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "timestamp": event.timestamp,
                "payload": event.payload,
                "failed_at": datetime.now(timezone.utc),
                "error_message": error_msg,
                "retry_count": retries
            }
            # Upsert by event_id to prevent duplicates
            await db.sync_dlq.replace_one({"event_id": event.event_id}, dlq_record, upsert=True)
            memory_sync_metrics.record_dead_letter()
            logger.error(f"Event {event.event_id} ({event.event_type}) pushed to DLQ after {retries} retries. Error: {error_msg}")
        except Exception as e:
            logger.critical(f"FAILED TO WRITE EVENT TO DLQ DATABASE: {str(e)}", exc_info=True)

    async def _worker_loop(self) -> None:
        """Core background task loop consuming and processing events"""
        while self._running:
            try:
                # Retrieve next event tuple from the queue
                event, retry_count = await self._queue.get()
                
                try:
                    if not self._sync_service:
                        raise RuntimeError("MemorySyncService is not registered on the EventQueue worker")

                    # Extract patient_id from payload
                    patient_id = event.payload.get("patient_id")
                    if not patient_id:
                        raise ValueError(f"Event payload missing 'patient_id' in event {event.event_id}")

                    # Execute synchronization
                    await self._sync_service.sync_patient(patient_id, event=event)
                    
                except Exception as exc:
                    logger.warning(
                        f"Attempt {retry_count + 1} failed for event {event.event_id} ({event.event_type}): {str(exc)}"
                    )
                    
                    # Log retry telemetry
                    memory_sync_metrics.record_failure()
                    
                    next_retry = retry_count + 1
                    if next_retry <= self.max_retries:
                        # Exponential backoff delay
                        delay = self.base_delay * (2 ** retry_count)
                        logger.info(f"Retrying event {event.event_id} in {delay:.1f} seconds (Retry {next_retry}/{self.max_retries})")
                        memory_sync_metrics.record_retry()
                        
                        # Re-enqueue in worker thread after delay
                        async def re_enqueue_after_delay(e, r_cnt, d):
                            await asyncio.sleep(d)
                            self._queue.put_nowait((e, r_cnt))
                            
                        asyncio.create_task(re_enqueue_after_delay(event, next_retry, delay))
                    else:
                        # Push to Dead-Letter Queue
                        await self._push_to_dlq(event, str(exc), retry_count)
                        
                finally:
                    self._queue.task_done()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Unexpected error in background EventQueue loop: {str(e)}", exc_info=True)
                await asyncio.sleep(1.0)
