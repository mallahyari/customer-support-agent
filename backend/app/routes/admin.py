"""
Admin routes for bot management.

Endpoints:
- GET /api/admin/bots - List all bots
- POST /api/admin/bots - Create new bot
- GET /api/admin/bots/{bot_id} - Get bot details
- PUT /api/admin/bots/{bot_id} - Update bot
- DELETE /api/admin/bots/{bot_id} - Delete bot
- POST /api/admin/bots/{bot_id}/avatar - Upload avatar
- DELETE /api/admin/bots/{bot_id}/avatar - Delete avatar
- POST /api/admin/bots/{bot_id}/regenerate-key - Regenerate API key
"""

import logging
import time
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.dependencies import get_current_admin
from app.models import AdminSession, Bot
from app.schemas import BotCreate, BotResponse, BotUpdate, MessageOnlyResponse

settings = get_settings()

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

    # Delete Qdrant vectors for this bot_id (Phase 4)
    try:
        from app.services.qdrant_client import delete_vectors

        await delete_vectors(bot_id)
        logger.info(f"Deleted Qdrant vectors for bot {bot_id}")
    except Exception as e:
        logger.error(f"Failed to delete Qdrant vectors for bot {bot_id}: {e}")
        # Don't fail the whole operation if Qdrant cleanup fails

    logger.info(f"Admin {admin.username} deleted bot: {bot_id} ({bot_name})")

    return MessageOnlyResponse(message=f"Bot '{bot_name}' deleted successfully")


@router.post("/bots/{bot_id}/avatar", response_model=BotResponse)
async def upload_avatar(
    bot_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    admin: AdminSession = Depends(get_current_admin),
):
    """
    Upload and process bot avatar.

    Validates file type using magic numbers, checks size, resizes to 64x64,
    and saves as PNG. Deletes old avatar if exists.

    Args:
        bot_id: Bot UUID
        file: Uploaded image file
        db: Database session
        admin: Current authenticated admin

    Returns:
        Updated BotResponse with new avatar_url

    Raises:
        HTTPException: 404 if bot not found, 400 if validation fails
    """
    # Get existing bot
    result = await db.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalar_one_or_none()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bot with id {bot_id} not found",
        )

    # Validate file size (max 500KB)
    contents = await file.read()
    if len(contents) > 500 * 1024:  # 500KB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 500KB limit",
        )

    # Validate file type using magic numbers (first few bytes)
    # PNG: 89 50 4E 47, JPEG: FF D8 FF, GIF: 47 49 46
    if not (
        contents.startswith(b"\x89PNG")  # PNG
        or contents.startswith(b"\xff\xd8\xff")  # JPEG
        or contents.startswith(b"GIF8")  # GIF
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format. Only PNG, JPEG, and GIF are supported.",
        )

    # Open image with Pillow
    try:
        from io import BytesIO

        image = Image.open(BytesIO(contents))

        # Convert to RGB if necessary (for transparency)
        if image.mode in ("RGBA", "LA", "P"):
            # Create white background
            background = Image.new("RGB", image.size, (255, 255, 255))
            if image.mode == "P":
                image = image.convert("RGBA")
            background.paste(image, mask=image.split()[-1] if image.mode in ("RGBA", "LA") else None)
            image = background

        # Resize to 64x64
        image = image.resize((64, 64), Image.Resampling.LANCZOS)

    except Exception as e:
        logger.error(f"Failed to process image: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process image: {str(e)}",
        )

    # Create avatars directory if not exists
    avatar_dir = Path(settings.upload_path) / "avatars"
    avatar_dir.mkdir(parents=True, exist_ok=True)

    # Delete old avatar if exists
    old_avatars = list(avatar_dir.glob(f"{bot_id}_*.png"))
    for old_avatar in old_avatars:
        old_avatar.unlink()
        logger.info(f"Deleted old avatar: {old_avatar}")

    # Save new avatar
    timestamp = int(time.time())
    avatar_filename = f"{bot_id}_{timestamp}.png"
    avatar_path = avatar_dir / avatar_filename

    image.save(avatar_path, format="PNG", optimize=True)

    # Update bot avatar_url
    bot.avatar_url = f"/api/public/avatar/{bot_id}"

    await db.commit()
    await db.refresh(bot)

    logger.info(f"Admin {admin.username} uploaded avatar for bot: {bot.id} ({bot.name})")

    return bot


@router.delete("/bots/{bot_id}/avatar", response_model=MessageOnlyResponse)
async def delete_avatar(
    bot_id: str,
    db: AsyncSession = Depends(get_db),
    admin: AdminSession = Depends(get_current_admin),
):
    """
    Delete bot avatar.

    Removes avatar file from disk and clears avatar_url.

    Args:
        bot_id: Bot UUID
        db: Database session
        admin: Current authenticated admin

    Returns:
        Success message

    Raises:
        HTTPException: 404 if bot not found or avatar doesn't exist
    """
    # Get existing bot
    result = await db.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalar_one_or_none()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bot with id {bot_id} not found",
        )

    # Find and delete avatar files
    avatar_dir = Path(settings.upload_path) / "avatars"
    avatar_files = list(avatar_dir.glob(f"{bot_id}_*.png"))

    if not avatar_files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No avatar found for bot {bot_id}",
        )

    # Delete all avatar files for this bot
    for avatar_file in avatar_files:
        avatar_file.unlink()
        logger.info(f"Deleted avatar file: {avatar_file}")

    # Clear avatar_url
    bot.avatar_url = None

    await db.commit()
    await db.refresh(bot)

    logger.info(f"Admin {admin.username} deleted avatar for bot: {bot.id} ({bot.name})")

    return MessageOnlyResponse(message="Avatar deleted successfully")


@router.post("/bots/{bot_id}/regenerate-key", response_model=BotResponse)
async def regenerate_api_key(
    bot_id: str,
    db: AsyncSession = Depends(get_db),
    admin: AdminSession = Depends(get_current_admin),
):
    """
    Regenerate bot API key.

    Generates a new UUID for the bot's API key. The old key will immediately
    become invalid.

    Args:
        bot_id: Bot UUID
        db: Database session
        admin: Current authenticated admin

    Returns:
        Updated BotResponse with new api_key

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

    # Generate new API key (UUID will be auto-generated by generate_uuid)
    from app.models import generate_uuid

    old_key = bot.api_key
    bot.api_key = generate_uuid()

    await db.commit()
    await db.refresh(bot)

    logger.info(
        f"Admin {admin.username} regenerated API key for bot: {bot.id} ({bot.name})"
    )
    logger.warning(f"Old API key invalidated: {old_key[:8]}...")

    return bot


@router.post("/bots/{bot_id}/ingest", response_model=MessageOnlyResponse)
async def ingest_content(
    bot_id: str,
    db: AsyncSession = Depends(get_db),
    admin: AdminSession = Depends(get_current_admin),
):
    """
    Ingest content for a bot and generate embeddings.

    Reads bot's source_type and source_content, scrapes/processes the content,
    chunks it, generates embeddings, and stores in Qdrant.

    Args:
        bot_id: Bot UUID
        db: Database session
        admin: Current authenticated admin

    Returns:
        Success message with chunk count

    Raises:
        HTTPException: 404 if bot not found, 400 if ingestion fails
    """
    # Get existing bot
    result = await db.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalar_one_or_none()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bot with id {bot_id} not found",
        )

    if not bot.source_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bot has no source content configured",
        )

    logger.info(
        f"Starting ingestion for bot {bot_id} ({bot.name}): "
        f"{bot.source_type} - {bot.source_content[:100]}"
    )

    try:
        # Import services
        from app.services.chunker import chunk_text
        from app.services.embeddings import embed_and_store
        from app.services.qdrant_client import delete_vectors
        from app.services.scraper import scrape_url

        # Get content based on source type
        if bot.source_type == "url":
            logger.info(f"Scraping URL: {bot.source_content}")
            text, error = await scrape_url(bot.source_content)

            if error:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to scrape URL: {error}",
                )

            source = bot.source_content

        elif bot.source_type == "text":
            logger.info("Using direct text input")
            text = bot.source_content
            source = "direct_input"

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported source type: {bot.source_type}",
            )

        if not text or not text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No content could be extracted",
            )

        logger.info(f"Extracted {len(text)} characters of text")

        # Chunk the text
        logger.info("Chunking text...")
        chunks = chunk_text(text, source=source)

        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create chunks from content",
            )

        logger.info(f"Created {len(chunks)} chunks")

        # Delete old vectors first
        logger.info("Clearing old vectors...")
        await delete_vectors(bot_id)

        # Generate embeddings and store
        logger.info("Generating embeddings and storing in Qdrant...")
        vector_count = await embed_and_store(bot_id, chunks)

        # Update bot timestamp
        bot.updated_at = bot.updated_at  # Trigger SQLAlchemy update
        await db.commit()

        logger.info(
            f"Admin {admin.username} completed ingestion for bot {bot_id}: "
            f"{vector_count} vectors stored"
        )

        return MessageOnlyResponse(
            message=f"Successfully ingested content: {len(chunks)} chunks, "
            f"{vector_count} embeddings generated"
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Ingestion failed for bot {bot_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}",
        )
