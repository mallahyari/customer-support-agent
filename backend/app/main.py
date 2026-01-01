"""
FastAPI application entry point.

This module initializes the FastAPI app, sets up CORS middleware,
and mounts all API routes.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    Handles:
    - Creating data directories
    - Database initialization (Phase 1.2)
    - Creating admin user (Phase 1.3)
    """
    from app.database import init_db, close_db

    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    # Create necessary directories
    settings.ensure_data_directories()
    logger.info("Data directories initialized")

    # Initialize database (create tables)
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    # Create admin user on startup (Phase 1.3)
    try:
        from app.routes.auth import ADMIN_CREDENTIALS
        from app.services.auth_service import hash_password

        if ADMIN_CREDENTIALS["password_hash"] is None:
            ADMIN_CREDENTIALS["password_hash"] = hash_password(settings.admin_password)
            logger.info(f"Admin user initialized: {settings.admin_username}")
        else:
            logger.info("Admin credentials already initialized")
    except Exception as e:
        logger.error(f"Failed to initialize admin user: {e}")
        raise

    # Initialize Qdrant collection (Phase 3.1)
    try:
        from app.services.qdrant_client import init_collection

        await init_collection()
        logger.info("Qdrant collection initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Qdrant collection: {e}")
        raise

    yield

    # Cleanup on shutdown
    logger.info("Shutting down application")
    await close_db()
    logger.info("Database connections closed")

    # Close Qdrant client
    from app.services.qdrant_client import close_client

    await close_client()


# Create FastAPI app
app = FastAPI(
    title="Chirp AI Chatbot API",
    version="0.1.0",
    description="Open-source AI chatbot widget backend with RAG",
    lifespan=lifespan
)

# Configure CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/api/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns:
        JSON response with service status, timestamp, and component health
    """
    from app.services.qdrant_client import health_check as qdrant_health

    # Check Qdrant health
    qdrant_status = await qdrant_health()

    # Overall health is healthy only if all components are healthy
    overall_healthy = qdrant_status.get("healthy", False)

    return JSONResponse(
        content={
            "status": "healthy" if overall_healthy else "unhealthy",
            "service": "chirp-api",
            "version": "0.1.0",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "database": "healthy",  # SQLite is always available if app started
                "qdrant": qdrant_status,
            },
        }
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": "Chirp AI Chatbot API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/health"
    }


# Phase 1.3: Mount auth routes
from app.routes import auth
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])

# Phase 2.1: Mount admin routes
from app.routes import admin
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])

# Phase 2.2: Mount public routes
from app.routes import public
app.include_router(public.router, prefix="/api/public", tags=["Public"])

# Phase 5: Mount chat routes
from app.routes import chat
app.include_router(chat.router, prefix="/api", tags=["Chat"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
