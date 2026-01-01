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
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    # Create necessary directories
    settings.ensure_data_directories()
    logger.info("Data directories initialized")

    # TODO Phase 1.2: Initialize database
    # TODO Phase 1.3: Create admin user if not exists

    yield

    # Cleanup on shutdown
    logger.info("Shutting down application")


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
        JSON response with service status and timestamp
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "chirp-api",
            "version": "0.1.0",
            "timestamp": datetime.utcnow().isoformat(),
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


# TODO Phase 1.3: Mount auth routes
# from app.routes import auth
# app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])

# TODO Phase 2.1: Mount admin routes
# from app.routes import admin
# app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])

# TODO Phase 5.3: Mount public routes
# from app.routes import public
# app.include_router(public.router, prefix="/api/public", tags=["Public"])

# TODO Phase 5.3: Mount chat routes
# from app.routes import chat
# app.include_router(chat.router, prefix="/api", tags=["Chat"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
