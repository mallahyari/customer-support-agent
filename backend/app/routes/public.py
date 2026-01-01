"""
Public routes for widget integration.

Endpoints:
- GET /api/public/avatar/{bot_id} - Serve bot avatar image
- GET /api/public/config/{bot_id} - Get public bot configuration
"""

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models import Bot
from app.schemas import BotPublicConfig

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


@router.get("/avatar/{bot_id}")
async def get_avatar(bot_id: str):
    """
    Serve bot avatar image.

    Public endpoint (no authentication required) for widget to fetch avatars.

    Args:
        bot_id: Bot UUID

    Returns:
        PNG image file

    Raises:
        HTTPException: 404 if avatar not found
    """
    # Check if avatar exists
    avatar_dir = Path(settings.upload_path) / "avatars"

    # Find avatar file for this bot (should be {bot_id}_*.png)
    avatar_files = list(avatar_dir.glob(f"{bot_id}_*.png"))

    if not avatar_files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Avatar for bot {bot_id} not found",
        )

    # Get the most recent avatar (in case there are multiple)
    avatar_path = max(avatar_files, key=lambda p: p.stat().st_mtime)

    return FileResponse(
        path=avatar_path,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=3600"},  # Cache for 1 hour
    )


@router.get("/config/{bot_id}", response_model=BotPublicConfig)
async def get_bot_config(
    bot_id: str,
    api_key: str = Query(..., description="Bot API key for authentication"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get public bot configuration for widget initialization.

    Widget calls this on load to get bot settings (name, welcome message,
    styling, etc.). Requires API key for authentication.

    Args:
        bot_id: Bot UUID
        api_key: Bot API key (query parameter)
        db: Database session

    Returns:
        Public bot configuration (no sensitive data)

    Raises:
        HTTPException: 401 if invalid bot_id or api_key, 404 if bot not found
    """
    logger.info(f"Widget config request for bot: {bot_id}")

    # Validate bot and API key
    result = await db.execute(
        select(Bot).where(
            Bot.id == bot_id,
            Bot.api_key == api_key,
        )
    )
    bot = result.scalar_one_or_none()

    if not bot:
        logger.warning(f"Invalid bot_id or api_key for config request: {bot_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bot_id or api_key",
        )

    logger.info(f"Returning config for bot: {bot.name} ({bot_id})")

    # Return public configuration (BotPublicConfig excludes sensitive fields)
    return BotPublicConfig.model_validate(bot)
