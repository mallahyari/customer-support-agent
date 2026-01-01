"""
Authentication service for admin users.

Provides password hashing, session token generation, and session management.
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import AdminSession

settings = get_settings()


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string (bcrypt hash)

    Note:
        bcrypt has a 72-byte password limit, so we truncate to 72 bytes
    """
    # Truncate password to 72 bytes (bcrypt limitation)
    password_bytes = password.encode('utf-8')[:72]

    # Generate salt and hash password
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)

    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against (bcrypt hash)

    Returns:
        True if password matches, False otherwise

    Note:
        Truncates password to 72 bytes to match bcrypt limitation
    """
    # Truncate password to 72 bytes (bcrypt limitation)
    password_bytes = plain_password.encode('utf-8')[:72]
    hashed_bytes = hashed_password.encode('utf-8')

    return bcrypt.checkpw(password_bytes, hashed_bytes)


def generate_session_token() -> str:
    """
    Generate a secure random session token.

    Returns:
        UUID v4 string for session token
    """
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """
    Hash a session token using SHA-256.

    Args:
        token: Plain text token

    Returns:
        SHA-256 hash of the token
    """
    return hashlib.sha256(token.encode()).hexdigest()


async def create_admin_session(
    db: AsyncSession, username: str, token: str
) -> AdminSession:
    """
    Create a new admin session.

    Args:
        db: Database session
        username: Admin username
        token: Plain text session token

    Returns:
        Created AdminSession object
    """
    # Hash the token before storage
    token_hash = hash_token(token)

    # Calculate expiry time
    expires_at = datetime.utcnow() + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    # Create session
    session = AdminSession(
        username=username, token_hash=token_hash, expires_at=expires_at
    )

    db.add(session)
    await db.commit()
    await db.refresh(session)

    return session


async def get_session_by_token(
    db: AsyncSession, token: str
) -> Optional[AdminSession]:
    """
    Get admin session by token.

    Args:
        db: Database session
        token: Plain text session token

    Returns:
        AdminSession if found and valid, None otherwise
    """
    token_hash = hash_token(token)

    result = await db.execute(
        select(AdminSession).where(AdminSession.token_hash == token_hash)
    )
    session = result.scalar_one_or_none()

    # Check if session exists and is not expired
    if session and session.expires_at > datetime.utcnow():
        return session

    # Clean up expired session if found
    if session:
        await db.delete(session)
        await db.commit()

    return None


async def delete_session(db: AsyncSession, session_id: str) -> bool:
    """
    Delete an admin session (logout).

    Args:
        db: Database session
        session_id: Session ID to delete

    Returns:
        True if deleted, False if not found
    """
    result = await db.execute(select(AdminSession).where(AdminSession.id == session_id))
    session = result.scalar_one_or_none()

    if session:
        await db.delete(session)
        await db.commit()
        return True

    return False


async def cleanup_expired_sessions(db: AsyncSession) -> int:
    """
    Clean up all expired sessions.

    Args:
        db: Database session

    Returns:
        Number of sessions deleted
    """
    result = await db.execute(
        select(AdminSession).where(AdminSession.expires_at < datetime.utcnow())
    )
    expired_sessions = result.scalars().all()

    count = len(expired_sessions)
    for session in expired_sessions:
        await db.delete(session)

    await db.commit()
    return count
