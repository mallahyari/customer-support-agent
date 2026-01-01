"""
SQLAlchemy ORM models for the database.

Models:
- Bot: Chatbot configuration and settings
- Conversation: Chat sessions between users and bots
- Message: Individual messages in conversations
- AdminSession: Admin user sessions for authentication
"""

import uuid
from datetime import datetime
from typing import List

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def generate_uuid() -> str:
    """Generate a UUID string for primary keys."""
    return str(uuid.uuid4())


class Bot(Base):
    """
    Chatbot configuration model.

    Stores all settings for a chatbot including appearance,
    knowledge source, and usage limits.
    """

    __tablename__ = "bots"

    # Primary Key
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)

    # Basic Info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    welcome_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Appearance
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    accent_color: Mapped[str] = mapped_column(String(7), default="#3B82F6")
    position: Mapped[str] = mapped_column(
        String(20), default="bottom-right"
    )  # bottom-right, bottom-left, bottom-center
    show_button_text: Mapped[bool] = mapped_column(Boolean, default=False)
    button_text: Mapped[str] = mapped_column(String(100), default="Chat with us")

    # Knowledge Source
    source_type: Mapped[str | None] = mapped_column(
        String(10), nullable=True
    )  # 'url' or 'text'
    source_content: Mapped[str | None] = mapped_column(Text, nullable=True)

    # API & Security
    api_key: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, default=generate_uuid, index=True
    )

    # Usage Tracking
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    message_limit: Mapped[int] = mapped_column(Integer, default=1000)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation", back_populates="bot", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Bot(id={self.id}, name={self.name})>"


class Conversation(Base):
    """
    Conversation/session model.

    Tracks chat sessions between end users and bots.
    """

    __tablename__ = "conversations"

    # Primary Key
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)

    # Foreign Keys
    bot_id: Mapped[str] = mapped_column(
        String, ForeignKey("bots.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Session tracking (from widget localStorage)
    session_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    bot: Mapped["Bot"] = relationship("Bot", back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, bot_id={self.bot_id}, session_id={self.session_id})>"


# Composite index for efficient lookups
Index("idx_conversation_bot_session", Conversation.bot_id, Conversation.session_id)


class Message(Base):
    """
    Message model.

    Stores individual messages in a conversation.
    """

    __tablename__ = "messages"

    # Primary Key
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)

    # Foreign Keys
    conversation_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Message Content
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # 'user' or 'assistant'
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="messages"
    )

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role})>"


class AdminSession(Base):
    """
    Admin session model.

    Stores admin user sessions for authentication.
    """

    __tablename__ = "admin_sessions"

    # Primary Key (session token)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)

    # Admin Info
    username: Mapped[str] = mapped_column(String(100), nullable=False)

    # Security
    token_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )  # SHA-256 hash

    # Expiry
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<AdminSession(id={self.id}, username={self.username})>"
