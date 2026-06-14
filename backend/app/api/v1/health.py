"""
Nura - Health Check Endpoint
System health monitoring with database connections
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings
from app.db.mongodb import get_connection_status
from app.db.qdrant import get_qdrant_status

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response schema"""
    status: str
    app: str
    environment: str
    mongodb: str
    qdrant: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    System health check endpoint
    
    Returns:
        - Overall system status
        - Application name and environment
        - Database connection status
        - Vector database connection status
    """
    
    # Check database connections
    mongodb_status = await get_connection_status()
    qdrant_status = await get_qdrant_status()
    
    # Determine overall health
    overall_status = "healthy"
    if mongodb_status != "connected" or qdrant_status != "connected":
        overall_status = "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        app=settings.APP_NAME,
        environment=settings.APP_ENV,
        mongodb=mongodb_status,
        qdrant=qdrant_status
    )