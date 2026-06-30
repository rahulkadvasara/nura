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
from app.api.v1 import health, auth, users, dashboard, doctor, admin, doctors, appointments, patient, payments, ai, reports, chat
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

    # Initialize Qdrant collections
    try:
        from app.services.vector_collection_service import get_vector_collection_service
        collection_service = get_vector_collection_service()
        await collection_service.initialize_all_collections()
    except Exception as e:
        import logging
        logging.getLogger("nura.main").error(f"Failed to auto-initialize Qdrant collections: {e}")

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
    
    # Initialize background EventQueue and register handlers
    try:
        from app.core.dependencies import get_event_queue, get_event_dispatcher, get_memory_sync_service
        event_queue = get_event_queue()
        event_dispatcher = get_event_dispatcher()
        memory_sync_service = get_memory_sync_service()
        
        event_queue.set_sync_service(memory_sync_service)
        event_queue.start()
        
        # Wildcard event handler to route all events to background EventQueue
        async def background_queue_pusher(event):
            event_queue.push(event)
            
        event_dispatcher.register_handler("*", background_queue_pusher)

        # Drug validation background event handler
        async def drug_validation_event_handler(event):
            try:
                payload = event.payload or {}
                patient_id = payload.get("patient_id")
                if patient_id:
                    from app.core.dependencies import get_drug_queue_manager
                    q_mgr = get_drug_queue_manager()
                    # Determine priority based on event type
                    priority = "high" if "Prescription" in event.event_type else "normal"
                    await q_mgr.enqueue(patient_id=patient_id, priority=priority)
            except Exception as ex:
                import logging
                logging.getLogger("nura.main").error(f"Error enqueuing background drug validation: {ex}")

        # Register event handlers for automatic validations
        event_dispatcher.register_handler("ReminderCreated", drug_validation_event_handler)
        event_dispatcher.register_handler("ReminderUpdated", drug_validation_event_handler)
        event_dispatcher.register_handler("PrescriptionCreated", drug_validation_event_handler)
        event_dispatcher.register_handler("PrescriptionUpdated", drug_validation_event_handler)
        event_dispatcher.register_handler("PatientProfileUpdated", drug_validation_event_handler)
        event_dispatcher.register_handler("MedicalHistoryUpdated", drug_validation_event_handler)
        event_dispatcher.register_handler("PipelineCompleted", drug_validation_event_handler)
        
        # Start drug validation background worker scheduler
        from app.services.drug_background.scheduler import get_drug_worker_scheduler
        drug_scheduler = get_drug_worker_scheduler()
        await drug_scheduler.start()

    except Exception as e:
        import logging
        logging.getLogger("nura.main").error(f"Failed to start EventQueue background worker or drug scheduler: {e}")

    yield
    
    # Shutdown background EventQueue worker
    try:
        from app.core.dependencies import get_event_queue
        event_queue = get_event_queue()
        await event_queue.stop()
    except Exception as e:
        import logging
        logging.getLogger("nura.main").error(f"Failed to stop EventQueue background worker: {e}")

    # Stop drug validation background worker scheduler
    try:
        from app.services.drug_background.scheduler import get_drug_worker_scheduler
        drug_scheduler = get_drug_worker_scheduler()
        await drug_scheduler.stop()
    except Exception as e:
        import logging
        logging.getLogger("nura.main").error(f"Failed to stop drug worker scheduler: {e}")
    
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
    app.include_router(
        ai.router,
        prefix=settings.API_V1_PREFIX + "/ai",
        tags=["ai"]
    )
    app.include_router(
        reports.router,
        prefix=settings.API_V1_PREFIX + "/reports",
        tags=["reports"]
    )
    app.include_router(
        chat.router,
        prefix=settings.API_V1_PREFIX + "/chat",
        tags=["chat"]
    )

    return app


app = create_application()