from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.pool import NullPool

from ..config import settings


async_engine = create_async_engine(
    url=settings.asyncpg_db_url,
    poolclass=NullPool,
    echo=True,
)

async_session = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
)
