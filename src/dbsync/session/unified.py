"""Unified database session management for dbsync-py.

This module provides a unified interface for both synchronous and asynchronous
database sessions with smart auto-detection and configuration support.
"""

__all__ = ["dbsync", "detect_async_context"]

import asyncio
import inspect

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ..config import get_default_async_mode
from .async_ import get_async_session_context
from .sync import get_session_context as get_sync_session_context


def detect_async_context() -> bool:
    """Detect if we're currently in an async context.

    Returns:
        True if in async context, False otherwise
    """
    try:
        # Check if there's a running event loop
        loop = asyncio.get_running_loop()
        if loop and loop.is_running():
            return True
    except RuntimeError:
        # No event loop running
        pass

    # Check if we're in an async function by examining the call stack
    frame = inspect.currentframe()
    try:
        while frame:
            if inspect.iscoroutinefunction(frame.f_code):
                return True
            # Check if the frame's function is async
            if hasattr(frame.f_locals.get("self"), "__await__"):
                return True
            frame = frame.f_back
    except Exception:
        pass
    finally:
        del frame

    return False


class DBSyncSession:
    """Unified database session that supports both sync and async operations."""

    def __init__(
        self,
        database_url: str | None = None,
        async_mode: bool | None = None,
        **engine_kwargs,
    ) -> None:
        """Initialize database session.

        Args:
            database_url: Database URL (uses config if None)
            async_mode: Explicitly set async (True) or sync (False) mode.
                       If None, will auto-detect or use configured default.
            **engine_kwargs: Additional engine parameters
        """
        self.database_url = database_url
        self.engine_kwargs = engine_kwargs
        self._session_context = None

        # Determine async mode
        if async_mode is None:
            # Try auto-detection first
            try:
                detected_async = detect_async_context()
                if detected_async:
                    self.async_mode = True
                else:
                    # Fall back to configured default
                    self.async_mode = get_default_async_mode()
            except Exception:
                # If detection fails, use configured default
                self.async_mode = get_default_async_mode()
        else:
            self.async_mode = async_mode

    def __enter__(self) -> Session:
        """Enter sync context manager."""
        if self.async_mode:
            raise RuntimeError(
                "Cannot use 'with' for async session. Use 'async with' instead."
            )

        self._session_context = get_sync_session_context(
            self.database_url, **self.engine_kwargs
        )
        return self._session_context.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit sync context manager."""
        if self._session_context:
            return self._session_context.__exit__(exc_type, exc_val, exc_tb)

    async def __aenter__(self) -> AsyncSession:
        """Enter async context manager."""
        if not self.async_mode:
            raise RuntimeError(
                "Cannot use 'async with' for sync session. Use 'with' instead."
            )

        self._session_context = get_async_session_context(
            self.database_url, **self.engine_kwargs
        )
        return await self._session_context.__aenter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        if self._session_context:
            return await self._session_context.__aexit__(exc_type, exc_val, exc_tb)


def dbsync(
    async_mode: bool | None = None,
    database_url: str | None = None,
    **engine_kwargs,
) -> DBSyncSession:
    """Get a database session that can be either sync or async.

    The session type is determined by:
    1. Explicit async_mode parameter
    2. Auto-detection of async context (if async_mode is None)
    3. Global default async mode configuration
    4. Default to sync mode

    Args:
        async_mode: Explicitly set async (True) or sync (False) mode.
                   If None, will auto-detect or use configured default.
        database_url: Database URL (uses config if None)
        **engine_kwargs: Additional engine parameters

    Returns:
        DBSyncSession (use with 'with' for sync or 'async with' for async)

    Examples:
        # Explicit sync mode
        with dbsync(async_mode=False) as session:
            result = session.execute(text("SELECT 1"))

        # Explicit async mode
        async with dbsync(async_mode=True) as session:
            result = await session.execute(text("SELECT 1"))

        # Auto-detection (in async function)
        async def my_function():
            async with dbsync() as session:  # Auto-detects async
                result = await session.execute(text("SELECT 1"))

        # Auto-detection (in sync function)
        def my_function():
            with dbsync() as session:  # Auto-detects sync
                result = session.execute(text("SELECT 1"))
    """
    return DBSyncSession(database_url, async_mode, **engine_kwargs)
