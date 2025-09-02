from functools import cached_property
from contextlib import asynccontextmanager, _AsyncGeneratorContextManager
from typing import AsyncGenerator, AsyncContextManager, Callable, Any
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from api.src.domain.music.services import YoutubeService
from api.src.domain.users.service import UserService
from api.src.domain.auth.service import AuthService
from api.src.infrastructure.dal.uow import SQLAlchemyUnitOfWork, AbstractUnitOfWork
from api.src.infrastructure.s3_client import S3Client
from api.src.infrastructure.dal.datasource import (
    SQLAlchemyUnitDataSource,
    AbstractUnitDataSource,
)

from api.src.infrastructure.settings import settings


class AppContainer:
    @cached_property
    def _sqlalchemy_async_engine(self) -> AsyncEngine:
        return create_async_engine(
            url=settings.postgres.url,
            poolclass=NullPool,
            # echo=True,
        )

    @cached_property
    def _sqlalchemy_async_session_factory(self) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(
            bind=self._sqlalchemy_async_engine,
            expire_on_commit=False,
        )

    @staticmethod
    @asynccontextmanager
    async def async_redis_client(url: str = settings.redis.app_url) -> AsyncGenerator[Redis, None]:
        """
        Async context manager for creating a temporary Redis client.

        Args:
            url (str): Redis connection URL. Defaults to ``settings.redis.app_url``.

        Yields:
            Redis: An active Redis client instance.

        Notes:
            - Opens a new connection for each context usage.
            - Ensures the connection is closed when the context exits.

        Example:
            async with RedisClientFactory.async_redis_client() as client:
                await client.set("foo", "bar")
        """
        async with Redis.from_url(url) as client:
            yield client

    @cached_property
    def async_s3_client(self) -> S3Client:
        """note: при необходимости можно размножить данный метод для доступа к разным buckets"""
        return S3Client(**settings.s3.config_dict)

    @cached_property
    def unit_of_work(self) -> AbstractUnitOfWork[AbstractUnitDataSource]:
        return SQLAlchemyUnitOfWork(
            session_factory=self._sqlalchemy_async_session_factory,
            datasource=SQLAlchemyUnitDataSource,
        )

    @cached_property
    def auth_service(self) -> AuthService:
        return AuthService(
            unit_of_work=self.unit_of_work,
            redis_client=self.async_redis_client,
        )

    @cached_property
    def user_service(self) -> UserService:
        return UserService(unit_of_work=self.unit_of_work)

    @cached_property
    def youtube_service(self) -> YoutubeService:
        return YoutubeService(
            s3_client=self.async_s3_client,
            redis_client=self.async_redis_client,
        )


app = AppContainer()
