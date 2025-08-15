from typing import AsyncGenerator

from redis import asyncio as redis
from redis.asyncio import Redis

from sqlalchemy.ext.asyncio import AsyncSession

from api.src.infrastructure.settings import settings
from api.src.infrastructure.database.config import async_session
from api.src.infrastructure.s3_client import S3Client


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


async def get_async_redis_client() -> AsyncGenerator[Redis, None]:
    async with redis.from_url(settings.redis.url) as client:
        yield client


async def get_async_s3_client() -> S3Client:
    return S3Client(**settings.s3.config_dict)
