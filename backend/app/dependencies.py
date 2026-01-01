"""
FastAPI dependencies for authentication and database access.

Provides reusable dependencies that can be injected into route handlers.
"""

from typing import Optional

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import AdminSession, Bot
from app.services.auth_service import get_session_by_token


async def get_current_admin(
    session_token: Optional[str] = Cookie(None), db: AsyncSession = Depends(get_db)
) -> AdminSession:
    """
    Dependency to get current authenticated admin.

    Validates session token from cookie and returns admin session.
    Raises 401 if not authenticated or session expired.

    Args:
        session_token: Session token from cookie
        db: Database session

    Returns:
        AdminSession object

    Raises:
        HTTPException: 401 if not authenticated or session invalid/expired
    """
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please log in.",
        )

    # Get session from database
    admin_session = await get_session_by_token(db, session_token)

    if not admin_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please log in again.",
        )

    return admin_session


async def get_current_admin_optional(
    session_token: Optional[str] = Cookie(None), db: AsyncSession = Depends(get_db)
) -> Optional[AdminSession]:
    """
    Optional dependency to get current admin if authenticated.

    Returns None if not authenticated instead of raising an exception.

    Args:
        session_token: Session token from cookie
        db: Database session

    Returns:
        AdminSession object if authenticated, None otherwise
    """
    if not session_token:
        return None

    return await get_session_by_token(db, session_token)


async def validate_bot_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> Bot:
    """
    Validate bot API key from X-API-Key header.

    Used by widget endpoints to authenticate requests.

    Args:
        x_api_key: API key from X-API-Key header
        db: Database session

    Returns:
        Bot object if API key is valid

    Raises:
        HTTPException: 401 if API key is missing or invalid
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Include X-API-Key header.",
        )

    # Look up bot by API key
    result = await db.execute(select(Bot).where(Bot.api_key == x_api_key))
    bot = result.scalar_one_or_none()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return bot
