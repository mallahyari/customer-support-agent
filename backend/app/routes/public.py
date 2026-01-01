"""
Public routes for widget integration.

Endpoints:
- GET /api/public/avatar/{bot_id} - Serve bot avatar image
- GET /api/public/config/{api_key} - Get public bot configuration (Phase 5)
"""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models import Bot

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
