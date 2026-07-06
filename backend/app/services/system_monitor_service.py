"""
Nura - System Monitor Service
Handles real-time health checks, system information diagnostics, and background job metrics tracking.
"""

import time
from datetime import datetime, timezone
import httpx
from typing import Dict, Any, List, Tuple

from app.core.config import settings
from app.db.mongodb import mongodb_connection
from app.db.qdrant import qdrant_connection
from app.repositories.reminder_repository import ReminderRepository
from app.schemas.system import (
    ServiceHealth,
    SystemInfoResponse,
    BackgroundJobItem,
    BackgroundJobResponse,
)

# Tracks module loading time as global application process initialization time
STARTUP_TIME = datetime.now(timezone.utc)


class SystemMonitorService:
    """Service to evaluate system component health, platform metadata, and background jobs"""

    def __init__(self, reminder_repository: ReminderRepository):
        self.reminder_repository = reminder_repository

    async def check_health(self) -> List[ServiceHealth]:
        """Verify status and check response latency of database and third-party API services"""
        now = datetime.now(timezone.utc)
        results = []

        # 1. API Gateway status (always healthy from within itself)
        results.append(
            ServiceHealth(
                name="API Gateway",
                status="healthy",
                latency_ms=0,
                message="Operational",
                last_checked=now,
            )
        )

        # 2. MongoDB Status
        mongo_start = time.time()
        try:
            is_mongo_connected = await mongodb_connection.is_connected()
            mongo_latency = int((time.time() - mongo_start) * 1000)
            if is_mongo_connected:
                results.append(
                    ServiceHealth(
                        name="MongoDB",
                        status="healthy",
                        latency_ms=mongo_latency,
                        message="Connected successfully",
                        last_checked=now,
                    )
                )
            else:
                results.append(
                    ServiceHealth(
                        name="MongoDB",
                        status="offline",
                        latency_ms=mongo_latency,
                        message="Database client disconnected or inaccessible",
                        last_checked=now,
                    )
                )
        except Exception as e:
            mongo_latency = int((time.time() - mongo_start) * 1000)
            results.append(
                ServiceHealth(
                    name="MongoDB",
                    status="offline",
                    latency_ms=mongo_latency,
                    message=str(e),
                    last_checked=now,
                )
            )

        # 3. Qdrant Status
        qdrant_start = time.time()
        try:
            is_qdrant_connected = await qdrant_connection.is_connected()
            qdrant_latency = int((time.time() - qdrant_start) * 1000)
            if is_qdrant_connected:
                results.append(
                    ServiceHealth(
                        name="Qdrant",
                        status="healthy",
                        latency_ms=qdrant_latency,
                        message="Connected successfully",
                        last_checked=now,
                    )
                )
            else:
                results.append(
                    ServiceHealth(
                        name="Qdrant",
                        status="offline",
                        latency_ms=qdrant_latency,
                        message="Vector store disconnected or inaccessible",
                        last_checked=now,
                    )
                )
        except Exception as e:
            qdrant_latency = int((time.time() - qdrant_start) * 1000)
            results.append(
                ServiceHealth(
                    name="Qdrant",
                    status="offline",
                    latency_ms=qdrant_latency,
                    message=str(e),
                    last_checked=now,
                )
            )

        # 4. Groq Status
        groq_start = time.time()
        if not settings.GROQ_API_KEY:
            results.append(
                ServiceHealth(
                    name="Groq AI",
                    status="offline",
                    latency_ms=0,
                    message="API key not configured",
                    last_checked=now,
                )
            )
        else:
            try:
                async with httpx.AsyncClient() as client:
                    headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
                    # Perform a lightweight models list request
                    response = await client.get("https://api.groq.com/openai/v1/models", headers=headers, timeout=2.0)
                    groq_latency = int((time.time() - groq_start) * 1000)
                    if response.status_code == 200:
                        results.append(
                            ServiceHealth(
                                name="Groq AI",
                                status="healthy",
                                latency_ms=groq_latency,
                                message="Connected successfully",
                                last_checked=now,
                            )
                        )
                    else:
                        results.append(
                            ServiceHealth(
                                name="Groq AI",
                                status="degraded",
                                latency_ms=groq_latency,
                                message=f"API returned status {response.status_code}",
                                last_checked=now,
                            )
                        )
            except Exception as e:
                groq_latency = int((time.time() - groq_start) * 1000)
                results.append(
                    ServiceHealth(
                        name="Groq AI",
                        status="offline",
                        latency_ms=groq_latency,
                        message=str(e),
                        last_checked=now,
                    )
                )

        # 5. Supabase Storage Status
        supabase_start = time.time()
        if not settings.SUPABASE_URL:
            results.append(
                ServiceHealth(
                    name="Supabase Storage",
                    status="offline",
                    latency_ms=0,
                    message="Supabase URL not configured",
                    last_checked=now,
                )
            )
        else:
            try:
                # Sanitize URL by removing rest subpath and trailing slashes
                base_url = settings.SUPABASE_URL
                if "/rest/v1" in base_url:
                    base_url = base_url.split("/rest/v1")[0]
                base_url = base_url.rstrip("/")

                async with httpx.AsyncClient() as client:
                    # Attempt health endpoint ping first
                    health_url = f"{base_url}/storage/v1/health"
                    try:
                        response = await client.get(health_url, timeout=2.0)
                        supabase_latency = int((time.time() - supabase_start) * 1000)
                        if response.status_code == 200:
                            results.append(
                                ServiceHealth(
                                    name="Supabase Storage",
                                    status="healthy",
                                    latency_ms=supabase_latency,
                                    message="Connected successfully",
                                    last_checked=now,
                                )
                            )
                            return results
                    except Exception:
                        pass

                    # Fallback check targeting buckets API endpoint
                    bucket_url = f"{base_url}/storage/v1/bucket"
                    headers = {"Authorization": f"Bearer {settings.SUPABASE_ANON_KEY or settings.SUPABASE_SERVICE_ROLE_KEY}"}
                    response = await client.get(bucket_url, headers=headers, timeout=2.0)
                    supabase_latency = int((time.time() - supabase_start) * 1000)
                    if response.status_code in (200, 401, 403):
                        results.append(
                            ServiceHealth(
                                name="Supabase Storage",
                                status="healthy",
                                latency_ms=supabase_latency,
                                message="Connected successfully",
                                last_checked=now,
                            )
                        )
                    else:
                        results.append(
                            ServiceHealth(
                                name="Supabase Storage",
                                status="degraded",
                                latency_ms=supabase_latency,
                                message=f"Service returned status {response.status_code}",
                                last_checked=now,
                            )
                        )
            except Exception as e:
                supabase_latency = int((time.time() - supabase_start) * 1000)
                results.append(
                    ServiceHealth(
                        name="Supabase Storage",
                        status="offline",
                        latency_ms=supabase_latency,
                        message=str(e),
                        last_checked=now,
                    )
                )

        return results

    def get_system_info(self) -> SystemInfoResponse:
        """Calculate system uptime and retrieve config environment variables"""
        now = datetime.now(timezone.utc)
        uptime_seconds = (now - STARTUP_TIME).total_seconds()
        return SystemInfoResponse(
            version="1.0.0",
            environment=settings.APP_ENV,
            startup_time=STARTUP_TIME,
            uptime_seconds=uptime_seconds,
        )

    async def get_background_jobs(self) -> BackgroundJobResponse:
        """Aggregate stats for background task executions"""
        now = datetime.now(timezone.utc)

        # Retrieve reminders query stats
        # status can be: active, completed, cancelled
        queued_count = await self.reminder_repository.collection.count_documents(
            {"status": "active", "scheduled_time": {"$gt": now}}
        )
        running_count = await self.reminder_repository.collection.count_documents(
            {"status": "active", "scheduled_time": {"$lte": now}}
        )
        completed_count = await self.reminder_repository.collection.count_documents(
            {"status": "completed"}
        )
        cancelled_count = await self.reminder_repository.collection.count_documents(
            {"status": "cancelled"}
        )

        # Determine last execution from completed reminders
        last_exec_cursor = self.reminder_repository.collection.find(
            {"status": "completed"}
        ).sort("updated_at", -1).limit(1)
        last_exec_list = await last_exec_cursor.to_list(length=1)
        last_execution = last_exec_list[0].get("updated_at") if last_exec_list else None

        # Determine next scheduled execution
        next_exec_cursor = self.reminder_repository.collection.find(
            {"status": "active", "scheduled_time": {"$gt": now}}
        ).sort("scheduled_time", 1).limit(1)
        next_exec_list = await next_exec_cursor.to_list(length=1)
        next_execution = next_exec_list[0].get("scheduled_time") if next_exec_list else None

        reminder_jobs = BackgroundJobItem(
            status="active",
            running=running_count,
            completed=completed_count,
            failed=cancelled_count,  # cancel/failed count
            queued=queued_count,
            last_execution=last_execution,
            next_execution=next_execution,
        )

        # Stub other jobs as 'Not configured'
        not_configured_job = BackgroundJobItem(
            status="Not configured",
            running=0,
            completed=0,
            failed=0,
            queued=0,
            last_execution=None,
            next_execution=None,
        )

        return BackgroundJobResponse(
            reminder_jobs=reminder_jobs,
            notification_jobs=not_configured_job,
            ai_jobs=not_configured_job,
            failed_jobs=not_configured_job,
        )
