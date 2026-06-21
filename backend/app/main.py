"""
Nura - AI-Powered Healthcare Assistant Platform
Main FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.mongodb import connect_to_mongodb, close_mongodb_connection, get_database
from app.db.qdrant import connect_to_qdrant, close_qdrant_connection
from app.db.init import setup_database
from app.api.v1 import health, auth, users
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Request, HTTPException, status


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    setup_logging()
    await connect_to_mongodb()
    await connect_to_qdrant()

    # Initialize collections and indexes (idempotent)
    try:
        db = get_database()
        await setup_database(db)
    except RuntimeError:
        # MongoDB not connected (e.g. dev without DB) — skip index setup
        pass
    
    yield
    
    # Shutdown
    await close_mongodb_connection()
    await close_qdrant_connection()


def create_application() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        description="AI-Powered Healthcare Assistant Platform",
        lifespan=lifespan
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom exception handlers for API contract consistency
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = []
        for error in exc.errors():
            loc = " -> ".join(str(x) for x in error["loc"])
            errors.append(f"{loc}: {error['msg']}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "message": "Validation failed",
                "errors": errors
            }
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.detail,
                "errors": None
            }
        )

    # Include routers
    app.include_router(
        health.router,
        prefix=settings.API_V1_PREFIX,
        tags=["health"]
    )
    app.include_router(
        auth.router,
        prefix=settings.API_V1_PREFIX + "/auth",
        tags=["auth"]
    )
    app.include_router(
        users.router,
        prefix=settings.API_V1_PREFIX + "/users",
        tags=["users"]
    )

    return app


app = create_application()