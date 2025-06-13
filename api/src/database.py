from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from config import settings


async_engine = create_async_engine(
    url=settings.asyncpg_db_url,
    poolclass=NullPool,
    echo=True,
)

async_session = async_sessionmaker(
    engine=async_engine,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Async generator yields main async session for api.

    Yields:
        AsyncGenerator
    """
    async with async_session() as session:
        yield session
