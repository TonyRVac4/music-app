from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Callable, Generic, TypeVar, AsyncContextManager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.src.infrastructure.dal.datasource import AbstractUnitDataSource

TUnitDataSource = TypeVar("TUnitDataSource")


class AbstractUnitOfWork(ABC, Generic[TUnitDataSource]):
    @abstractmethod
    def begin(self) -> AsyncContextManager[TUnitDataSource]:
        pass

    @abstractmethod
    def execute(self) -> AsyncContextManager[TUnitDataSource]:
        pass


class SQLAlchemyUnitOfWork(AbstractUnitOfWork):
    """
    SQLAlchemy implementation of Unit of Work pattern for managing dal transactions.

    This class provides two main contexts for dal operations:
    - `begin()`: For write operations with automatic commit
    - `execute()`: For read operations without automatic commit

    The Unit of Work encapsulates the session management and ensures that all
    repository operations within a single unit are executed within the same
    dal transaction.

    Attributes:
        _session_factory: Factory for creating SQLAlchemy async sessions
        _datasource: Factory function that creates datasource with repositories

    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        datasource: Callable[[AsyncSession], AbstractUnitDataSource],
    ) -> None:
        self._session_factory = session_factory
        self._datasource = datasource

    @asynccontextmanager
    async def begin(self) -> AsyncGenerator[AbstractUnitDataSource, None]:
        """
        Async context manager for create, update, delete operations with automatic commit.

        Yields:
            AbstractUnitDataSource: Datasource instance with all repositories
                                   configured for the current session
        """
        async with self._session_factory() as session:
            async with session.begin() as transaction:
                yield self._datasource(session)
                await transaction.commit()

    @asynccontextmanager
    async def execute(self) -> AsyncGenerator[AbstractUnitDataSource, None]:
        """
        Async context manager for read operations without automatic commit.
        Yields:
            AbstractUnitDataSource: Datasource instance with all repositories
                                   configured for the current session
        """
        async with self._session_factory() as session:
            yield self._datasource(session)
