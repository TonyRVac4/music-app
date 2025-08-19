from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession

from api.src.domain.users.repository import SQLAlchemyUserRepository
from api.src.domain.auth.repository import SQLAlchemyRefreshTokenRepository
from api.src.infrastructure.database.repository import AbstractSQLAlchemyRepository


class AbstractUnitDataSource(ABC):
    @property
    @abstractmethod
    def users(self) -> AbstractSQLAlchemyRepository:
        pass

    @property
    @abstractmethod
    def refresh_tokens(self) -> AbstractSQLAlchemyRepository:
        pass


class SQLAlchemyUnitDataSource(AbstractUnitDataSource):
    """
    Encapsulates all project repositories. Available through unit of work class.
    """
    def __init__(self, session: AsyncSession):
        self._session = session

    @property
    def users(self) -> AbstractSQLAlchemyRepository:
        return SQLAlchemyUserRepository(session=self._session)

    @property
    def refresh_tokens(self) -> AbstractSQLAlchemyRepository:
        return SQLAlchemyRefreshTokenRepository(session=self._session)
