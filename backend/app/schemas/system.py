"""
Nura - System Observability and Maintenance Schemas
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class ServiceHealth(BaseModel):
    """Health status details of a single subsystem"""
    name: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status (healthy, degraded, offline)")
    latency_ms: int = Field(..., description="Roundtrip latency in milliseconds")
    message: str = Field(..., description="Additional status message")
    last_checked: datetime = Field(..., description="Timestamp of when the service was last checked")


class PlatformHealthResponse(BaseModel):
    """Collection of service health checks"""
    services: List[ServiceHealth] = Field(..., description="List of monitored services health status")


class SystemInfoResponse(BaseModel):
    """Application metadata and uptime details"""
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Deployment environment")
    startup_time: datetime = Field(..., description="System startup timestamp")
    uptime_seconds: float = Field(..., description="Current system uptime in seconds")


class BackgroundJobItem(BaseModel):
    """Performance metrics for a background job category"""
    status: str = Field(..., description="Subsystem status (active, healthy, degraded, or Not configured)")
    running: int = Field(..., description="Count of running tasks")
    completed: int = Field(..., description="Count of completed tasks")
    failed: int = Field(..., description="Count of failed tasks")
    queued: int = Field(..., description="Count of queued tasks")
    last_execution: Optional[datetime] = Field(None, description="Timestamp of last execution")
    next_execution: Optional[datetime] = Field(None, description="Timestamp of next scheduled execution")


class BackgroundJobResponse(BaseModel):
    """Consolidated background tasks monitoring schema"""
    reminder_jobs: BackgroundJobItem = Field(..., description="Reminder background job status")
    notification_jobs: BackgroundJobItem = Field(..., description="Notification background job status")
    ai_jobs: BackgroundJobItem = Field(..., description="AI background job status")
    failed_jobs: BackgroundJobItem = Field(..., description="Failed background job status")


class MaintenanceResponse(BaseModel):
    """Operation result payload for system maintenance tasks"""
    success: bool = Field(default=True, description="Maintenance operation success status")
    message: str = Field(..., description="Execution summary message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Execution counts or details")
