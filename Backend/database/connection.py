"""Database connection and session management for SkepticAI.

This module handles the async SQLAlchemy engine, session factory,
and provides utilities for initializing and closing the database connection.
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

load_dotenv()


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# Global engine and session factory (initialized on startup)
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _get_database_url() -> str:
    """Get the database URL from environment variables.

    Returns:
        The DATABASE_URL from environment, converted to use asyncpg driver,
        with an explicit ``ssl=require`` param (Neon requires SSL, and
        asyncpg does not understand the libpq-style ``sslmode`` param).

    Raises:
        RuntimeError: If DATABASE_URL is not set.
    """
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set. "
            "Please configure it in your .env file."
        )
    # Convert sync postgresql:// to async postgresql+asyncpg://
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    # Remove parameters that asyncpg doesn't support (channel_binding, sslmode)
    # asyncpg uses 'ssl' parameter instead of 'sslmode' — add it explicitly
    # since Neon requires SSL on every connection.
    if "?" in url:
        base, query = url.split("?", 1)
        params = query.split("&")
        params = [
            p for p in params
            if not p.startswith("channel_binding=") and not p.startswith("sslmode=")
        ]
        params.append("ssl=require")
        url = base + "?" + "&".join(params)
    else:
        url = url + "?ssl=require"
    return url


def init_db() -> None:
    """Initialize the database engine and session factory.

    This should be called once at application startup.
    Uses connection pooling appropriate for Neon (pool_pre_ping for resilience).
    """
    global _engine, _session_factory

    database_url = _get_database_url()

    # Neon supports standard PostgreSQL connection strings.
    # Use asyncpg driver for async operations.
    # pool_pre_ping helps with Neon's connection lifecycle (handles cold starts).
    _engine = create_async_engine(
        database_url,
        echo=False,  # Set to True for SQL debugging
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,  # Recycle connections every 30 minutes
    )

    _session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


async def close_db() -> None:
    """Close the database engine and clean up connections.

    This should be called at application shutdown.
    """
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session.

    Usage:
        async with get_session() as session:
            # Use session for database operations
            ...

    Yields:
        An AsyncSession instance.

    Raises:
        RuntimeError: If init_db() has not been called.
    """
    if _session_factory is None:
        raise RuntimeError(
            "Database not initialized. Call init_db() at application startup."
        )

    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def health_check() -> bool:
    """Check if the database is reachable.

    Returns:
        True if database is reachable, False otherwise.
    """
    if _engine is None:
        return False
    try:
        from sqlalchemy import text
        async with _engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False