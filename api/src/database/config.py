from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.pool import NullPool

from api.src.settings import settings


async_engine = create_async_engine(
    url=settings.postgres.url,
    poolclass=NullPool,
    echo=True,
)

async_session = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
)
