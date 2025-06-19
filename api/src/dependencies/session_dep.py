from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from api.src.database.config import async_session


async def get_async_session_with_commit() -> AsyncGenerator[AsyncSession, None]:
    """Async generator yields main async session for api with auto commit.

    Yields:
        AsyncGenerator
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        else:
            await session.close()


async def get_async_session_without_commit() -> AsyncGenerator[AsyncSession, None]:
    """Async generator yields main async session for api without autocommit.

    Yields:
        AsyncGenerator
    """
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            await session.close()
