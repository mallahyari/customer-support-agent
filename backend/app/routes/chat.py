"""
Chat endpoints for widget API.

Provides the main chat endpoint with SSE streaming for real-time responses.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Bot, Conversation, Message, generate_uuid
from app.schemas import ChatRequest
from app.services.chat_service import generate_response

logger = logging.getLogger(__name__)
router = APIRouter()

# Rate limiting configuration
RATE_LIMIT_WINDOW = 60  # seconds
MAX_MESSAGES_PER_WINDOW = 10  # messages per session per window
_rate_limit_cache: dict[str, list[datetime]] = {}


def check_rate_limit(session_id: str) -> tuple[bool, Optional[str]]:
    """
    Check if session has exceeded rate limit.

    Args:
        session_id: Session identifier

    Returns:
        Tuple of (is_allowed, error_message)
    """
    now = datetime.utcnow()
    window_start = now - timedelta(seconds=RATE_LIMIT_WINDOW)

    # Get recent requests for this session
    if session_id not in _rate_limit_cache:
        _rate_limit_cache[session_id] = []

    recent_requests = _rate_limit_cache[session_id]

    # Remove old requests outside the window
    recent_requests = [ts for ts in recent_requests if ts > window_start]
    _rate_limit_cache[session_id] = recent_requests

    # Check limit
    if len(recent_requests) >= MAX_MESSAGES_PER_WINDOW:
        return False, f"Rate limit exceeded: max {MAX_MESSAGES_PER_WINDOW} messages per {RATE_LIMIT_WINDOW} seconds"

    # Add current request
    _rate_limit_cache[session_id].append(now)

    return True, None


async def get_or_create_conversation(
    db: AsyncSession,
    bot_id: str,
    session_id: str,
) -> Conversation:
    """
    Get existing conversation or create new one.

    Args:
        db: Database session
        bot_id: Bot UUID
        session_id: Session identifier from widget

    Returns:
        Conversation instance
    """
    # Try to find existing conversation
    result = await db.execute(
        select(Conversation).where(
            Conversation.bot_id == bot_id,
            Conversation.session_id == session_id,
        )
    )
    conversation = result.scalar_one_or_none()

    if conversation:
        logger.info(f"Found existing conversation: {conversation.id}")
        return conversation

    # Create new conversation
    conversation = Conversation(
        id=generate_uuid(),
        bot_id=bot_id,
        session_id=session_id,
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)

    logger.info(f"Created new conversation: {conversation.id}")
    return conversation


async def get_conversation_history(
    db: AsyncSession,
    conversation_id: str,
    limit: int = 10,
) -> list[Message]:
    """
    Get recent messages from conversation.

    Args:
        db: Database session
        conversation_id: Conversation UUID
        limit: Maximum number of messages to retrieve

    Returns:
        List of Message instances (oldest first)
    """
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    messages = result.scalars().all()

    # Return in chronological order (oldest first)
    return list(reversed(messages))


async def save_messages(
    db: AsyncSession,
    conversation_id: str,
    user_message: str,
    assistant_message: str,
) -> None:
    """
    Save user and assistant messages to database.

    Args:
        db: Database session
        conversation_id: Conversation UUID
        user_message: User's message
        assistant_message: Assistant's response
    """
    # Save user message
    user_msg = Message(
        id=generate_uuid(),
        conversation_id=conversation_id,
        role="user",
        content=user_message,
    )
    db.add(user_msg)

    # Save assistant message
    assistant_msg = Message(
        id=generate_uuid(),
        conversation_id=conversation_id,
        role="assistant",
        content=assistant_message,
    )
    db.add(assistant_msg)

    await db.commit()
    logger.info(f"Saved 2 messages for conversation {conversation_id}")


async def stream_response(
    bot: Bot,
    conversation: Conversation,
    user_message: str,
    conversation_history: list[Message],
    db: AsyncSession,
):
    """
    Stream SSE response from chat service.

    Args:
        bot: Bot instance
        conversation: Conversation instance
        user_message: User's message
        conversation_history: Previous messages
        db: Database session

    Yields:
        SSE-formatted response chunks
    """
    # Accumulate response for saving
    full_response = ""

    try:
        # Generate streaming response
        async for token in generate_response(bot, user_message, conversation_history):
            full_response += token
            # Format as SSE event
            yield f"data: {token}\n\n"

        # Send completion signal
        yield "data: [DONE]\n\n"

        # Save messages to database
        await save_messages(db, conversation.id, user_message, full_response)

        # Increment bot message count
        bot.message_count += 1
        await db.commit()

        logger.info(
            f"Chat completed for bot {bot.id}: "
            f"{len(user_message)} chars in, {len(full_response)} chars out"
        )

    except Exception as e:
        logger.error(f"Error during streaming: {e}")
        yield f"data: Error: {str(e)}\n\n"
        yield "data: [DONE]\n\n"


@router.post("/chat")
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Main chat endpoint with SSE streaming.

    Validates bot, checks rate limits, retrieves context, and streams response.

    Args:
        request: Chat request with bot_id, api_key, session_id, message
        db: Database session

    Returns:
        StreamingResponse with SSE events

    Raises:
        HTTPException: 401 if invalid API key, 429 if rate limited, 404 if bot not found
    """
    logger.info(
        f"Chat request: bot={request.bot_id}, session={request.session_id}, "
        f"message_len={len(request.message)}"
    )

    # Validate bot and API key
    result = await db.execute(
        select(Bot).where(
            Bot.id == request.bot_id,
            Bot.api_key == request.api_key,
        )
    )
    bot = result.scalar_one_or_none()

    if not bot:
        logger.warning(f"Invalid bot_id or api_key: {request.bot_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bot_id or api_key",
        )

    # Check bot message limit
    if bot.message_count >= bot.message_limit:
        logger.warning(f"Bot {bot.id} has reached message limit: {bot.message_count}/{bot.message_limit}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Bot has reached its message limit ({bot.message_limit} messages)",
        )

    # Check rate limiting
    is_allowed, error_msg = check_rate_limit(request.session_id)
    if not is_allowed:
        logger.warning(f"Rate limit exceeded for session {request.session_id}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_msg,
        )

    # Get or create conversation
    conversation = await get_or_create_conversation(db, bot.id, request.session_id)

    # Get conversation history
    conversation_history = await get_conversation_history(db, conversation.id)

    # Stream response
    return StreamingResponse(
        stream_response(bot, conversation, request.message, conversation_history, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
