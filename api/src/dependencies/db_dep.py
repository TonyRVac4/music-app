from typing import AsyncGenerator

from redis import asyncio as redis
from redis.asyncio import Redis

from sqlalchemy.ext.asyncio import AsyncSession
from types_aiobotocore_s3 import Client

from api.src.config import settings
from api.src.database.config import async_session
from api.src.utils.s3_client import S3Client


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
    async with redis.from_url(settings.redis_db_url) as client:
        yield client


async def get_async_s3_client() -> AsyncGenerator[Client, None]:
    async with S3Client(**settings.s3_config) as client:
        yield client
