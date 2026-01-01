"""
Authentication routes for admin users.

Endpoints:
- POST /api/auth/login - Admin login
- POST /api/auth/logout - Admin logout
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.dependencies import get_current_admin
from app.models import AdminSession
from app.schemas import LoginRequest, LoginResponse, MessageOnlyResponse
from app.services.auth_service import (
    create_admin_session,
    delete_session,
    generate_session_token,
    verify_password,
)

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


# In-memory storage for admin credentials (for Phase 1.3 MVP)
# TODO Phase 2+: Move to database with proper user management
ADMIN_CREDENTIALS = {
    "username": settings.admin_username,
    "password_hash": None,  # Will be set on first startup
}


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    credentials: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)
):
    """
    Admin login endpoint.

    Validates credentials and creates a session.
    Sets session_token cookie on success.

    Args:
        credentials: Login credentials (username and password)
        response: FastAPI response object (for setting cookies)
        db: Database session

    Returns:
        LoginResponse with success message and username

    Raises:
        HTTPException: 401 if credentials are invalid
    """
    # Verify username
    if credentials.username != ADMIN_CREDENTIALS["username"]:
        logger.warning(f"Failed login attempt for username: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Verify password
    if not verify_password(credentials.password, ADMIN_CREDENTIALS["password_hash"]):
        logger.warning(f"Failed login attempt for user: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Generate session token
    token = generate_session_token()

    # Create session in database
    await create_admin_session(db, credentials.username, token)

    # Set secure HTTP-only cookie
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,  # Prevent JavaScript access
        secure=not settings.debug,  # HTTPS only in production
        samesite="lax",  # CSRF protection
        max_age=settings.access_token_expire_minutes * 60,  # Convert to seconds
    )

    logger.info(f"User logged in: {credentials.username}")

    return LoginResponse(message="Login successful", username=credentials.username)


@router.post("/logout", response_model=MessageOnlyResponse, status_code=status.HTTP_200_OK)
async def logout(
    response: Response,
    db: AsyncSession = Depends(get_db),
    admin: AdminSession = Depends(get_current_admin),
):
    """
    Admin logout endpoint.

    Deletes the session and clears the session cookie.

    Args:
        response: FastAPI response object (for clearing cookies)
        db: Database session
        admin: Current authenticated admin (from dependency)

    Returns:
        MessageOnlyResponse with success message
    """
    # Delete session from database
    await delete_session(db, admin.id)

    # Clear cookie
    response.delete_cookie(key=settings.session_cookie_name)

    logger.info(f"User logged out: {admin.username}")

    return MessageOnlyResponse(message="Logged out successfully")
