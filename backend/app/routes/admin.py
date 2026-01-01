"""
Admin routes for bot management.

Endpoints:
- GET /api/admin/bots - List all bots
- POST /api/admin/bots - Create new bot
- GET /api/admin/bots/{bot_id} - Get bot details
- PUT /api/admin/bots/{bot_id} - Update bot
- DELETE /api/admin/bots/{bot_id} - Delete bot
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_admin
from app.models import AdminSession, Bot
from app.schemas import BotCreate, BotResponse, BotUpdate, MessageOnlyResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/bots", response_model=List[BotResponse])
async def list_bots(
    db: AsyncSession = Depends(get_db),
    admin: AdminSession = Depends(get_current_admin),
):
    """
    List all bots.

    Returns list of all bots with their configuration and stats.

    Args:
        db: Database session
        admin: Current authenticated admin

    Returns:
        List of BotResponse objects
    """
    result = await db.execute(select(Bot).order_by(Bot.created_at.desc()))
    bots = result.scalars().all()

    logger.info(f"Admin {admin.username} listed {len(bots)} bots")

    return bots


@router.post("/bots", response_model=BotResponse, status_code=status.HTTP_201_CREATED)
async def create_bot(
    bot_data: BotCreate,
    db: AsyncSession = Depends(get_db),
    admin: AdminSession = Depends(get_current_admin),
):
    """
    Create a new bot.

    Generates unique ID and API key automatically.

    Args:
        bot_data: Bot configuration data
        db: Database session
        admin: Current authenticated admin

    Returns:
        Created BotResponse object

    Raises:
        HTTPException: 400 if validation fails
    """
    # Create new bot (UUID and API key generated automatically by model defaults)
    bot = Bot(**bot_data.model_dump())

    db.add(bot)
    await db.commit()
    await db.refresh(bot)

    logger.info(f"Admin {admin.username} created bot: {bot.id} ({bot.name})")

    return bot


@router.get("/bots/{bot_id}", response_model=BotResponse)
async def get_bot(
    bot_id: str,
    db: AsyncSession = Depends(get_db),
    admin: AdminSession = Depends(get_current_admin),
):
    """
    Get bot details by ID.

    Args:
        bot_id: Bot UUID
        db: Database session
        admin: Current authenticated admin

    Returns:
        BotResponse object

    Raises:
        HTTPException: 404 if bot not found
    """
    result = await db.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalar_one_or_none()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bot with id {bot_id} not found",
        )

    logger.info(f"Admin {admin.username} viewed bot: {bot.id} ({bot.name})")

    return bot


@router.put("/bots/{bot_id}", response_model=BotResponse)
async def update_bot(
    bot_id: str,
    bot_data: BotUpdate,
    db: AsyncSession = Depends(get_db),
    admin: AdminSession = Depends(get_current_admin),
):
    """
    Update bot configuration.

    Only updates fields that are provided (partial update).

    Args:
        bot_id: Bot UUID
        bot_data: Updated bot data (all fields optional)
        db: Database session
        admin: Current authenticated admin

    Returns:
        Updated BotResponse object

    Raises:
        HTTPException: 404 if bot not found
    """
    # Get existing bot
    result = await db.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalar_one_or_none()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bot with id {bot_id} not found",
        )

    # Update only provided fields
    update_data = bot_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(bot, field, value)

    await db.commit()
    await db.refresh(bot)

    logger.info(f"Admin {admin.username} updated bot: {bot.id} ({bot.name})")

    return bot


@router.delete("/bots/{bot_id}", response_model=MessageOnlyResponse)
async def delete_bot(
    bot_id: str,
    db: AsyncSession = Depends(get_db),
    admin: AdminSession = Depends(get_current_admin),
):
    """
    Delete a bot.

    Deletes the bot and all associated data (conversations, messages).
    Note: Qdrant vectors will be cleaned up in Phase 3.

    Args:
        bot_id: Bot UUID
        db: Database session
        admin: Current authenticated admin

    Returns:
        Success message

    Raises:
        HTTPException: 404 if bot not found
    """
    # Get existing bot
    result = await db.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalar_one_or_none()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bot with id {bot_id} not found",
        )

    bot_name = bot.name

    # Delete bot (cascade will handle conversations and messages)
    await db.delete(bot)
    await db.commit()

    # TODO Phase 3: Delete Qdrant vectors for this bot_id

    logger.info(f"Admin {admin.username} deleted bot: {bot_id} ({bot_name})")

    return MessageOnlyResponse(message=f"Bot '{bot_name}' deleted successfully")
