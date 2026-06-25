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
from app.api.v1 import health, auth, users, dashboard, doctor, admin, doctors, appointments, patient, payments
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

    # Initialize collections and indexes (idempotent) and run admin bootstrap
    try:
        db = get_database()
        await setup_database(db)

        # Admin bootstrap logic
        from app.repositories import UserRepository, AuditLogRepository
        from app.services import UserService, AdminBootstrapService
        
        user_repo = UserRepository(db.users)
        user_service = UserService(user_repo)
        audit_repo = AuditLogRepository(db.audit_logs)
        
        bootstrap_service = AdminBootstrapService(user_service, audit_repo)
        await bootstrap_service.bootstrap_admin()
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
    app.include_router(
        dashboard.router,
        prefix=settings.API_V1_PREFIX + "/dashboard",
        tags=["dashboard"]
    )
    app.include_router(
        doctor.router,
        prefix=settings.API_V1_PREFIX + "/doctor",
        tags=["doctor"]
    )
    app.include_router(
        admin.router,
        prefix=settings.API_V1_PREFIX + "/admin",
        tags=["admin"]
    )
    app.include_router(
        doctors.router,
        prefix=settings.API_V1_PREFIX + "/doctors",
        tags=["doctors"]
    )
    app.include_router(
        appointments.router,
        prefix=settings.API_V1_PREFIX + "/appointments",
        tags=["appointments"]
    )
    app.include_router(
        patient.router,
        prefix=settings.API_V1_PREFIX + "/patient",
        tags=["patient"]
    )
    app.include_router(
        payments.router,
        prefix=settings.API_V1_PREFIX + "/payments",
        tags=["payments"]
    )

    return app


app = create_application()