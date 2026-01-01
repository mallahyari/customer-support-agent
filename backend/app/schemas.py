"""
Pydantic schemas for request/response validation.

These schemas are used for API input validation and serialization.
Separate from SQLAlchemy models to maintain clean separation of concerns.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Bot Schemas
# =============================================================================


class BotBase(BaseModel):
    """Base schema for Bot with common fields."""

    name: str = Field(..., min_length=1, max_length=255, description="Bot name")
    welcome_message: Optional[str] = Field(None, description="Welcome message for users")
    accent_color: str = Field(
        "#3B82F6", pattern=r"^#[0-9A-Fa-f]{6}$", description="Hex color code"
    )
    position: str = Field(
        "bottom-right",
        pattern=r"^(bottom-right|bottom-left|bottom-center)$",
        description="Widget position",
    )
    show_button_text: bool = Field(False, description="Show text on chat button")
    button_text: str = Field(
        "Chat with us", min_length=1, max_length=100, description="Chat button text"
    )
    source_type: Optional[str] = Field(
        None, pattern=r"^(url|text)$", description="Knowledge source type"
    )
    source_content: Optional[str] = Field(None, description="URL or text content")
    message_limit: int = Field(
        1000, ge=1, le=1000000, description="Monthly message limit"
    )


class BotCreate(BotBase):
    """Schema for creating a new bot."""

    pass


class BotUpdate(BaseModel):
    """Schema for updating a bot (all fields optional)."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    welcome_message: Optional[str] = None
    accent_color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    position: Optional[str] = Field(
        None, pattern=r"^(bottom-right|bottom-left|bottom-center)$"
    )
    show_button_text: Optional[bool] = None
    button_text: Optional[str] = Field(None, min_length=1, max_length=100)
    source_type: Optional[str] = Field(None, pattern=r"^(url|text)$")
    source_content: Optional[str] = None
    message_limit: Optional[int] = Field(None, ge=1, le=1000000)


class BotResponse(BotBase):
    """Schema for bot response."""

    id: str
    avatar_url: Optional[str]
    api_key: str
    message_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BotPublicConfig(BaseModel):
    """Public bot configuration for widget (no sensitive data)."""

    name: str
    welcome_message: Optional[str]
    avatar_url: Optional[str]
    accent_color: str
    position: str
    show_button_text: bool
    button_text: str

    model_config = {"from_attributes": True}


# =============================================================================
# Conversation Schemas
# =============================================================================


class ConversationBase(BaseModel):
    """Base schema for Conversation."""

    bot_id: str
    session_id: str


class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation."""

    pass


class ConversationResponse(ConversationBase):
    """Schema for conversation response."""

    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Message Schemas
# =============================================================================


class MessageBase(BaseModel):
    """Base schema for Message."""

    role: str = Field(..., pattern=r"^(user|assistant)$", description="Message role")
    content: str = Field(..., min_length=1, description="Message content")


class MessageCreate(MessageBase):
    """Schema for creating a new message."""

    conversation_id: str


class MessageResponse(MessageBase):
    """Schema for message response."""

    id: str
    conversation_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Chat Schemas (for widget API)
# =============================================================================


class ChatMessage(BaseModel):
    """Schema for a chat message in conversation history."""

    role: str = Field(..., pattern=r"^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    """Schema for chat request from widget."""

    bot_id: str
    api_key: str
    session_id: str
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_history: list[ChatMessage] = Field(default_factory=list, max_length=50)


# =============================================================================
# Admin/Auth Schemas
# =============================================================================


class LoginRequest(BaseModel):
    """Schema for admin login request."""

    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """Schema for login response."""

    message: str
    username: str


class AdminSessionResponse(BaseModel):
    """Schema for admin session response."""

    id: str
    username: str
    expires_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Generic Response Schemas
# =============================================================================


class MessageOnlyResponse(BaseModel):
    """Generic response with just a message."""

    message: str


class ErrorResponse(BaseModel):
    """Error response schema."""

    detail: str


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str
    service: str
    version: str
    timestamp: str
