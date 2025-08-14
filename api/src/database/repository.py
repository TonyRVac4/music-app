import logging
from typing import TypeVar
from abc import ABC, abstractmethod

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession


logger = logging.getLogger("my_app")

DTOModelType = TypeVar("DTOModelType", bound=BaseModel)


class AbstractSQLAlchemyRepository(ABC):
    def __init__(self, session: AsyncSession):
        self._session = session

    @abstractmethod
    async def create(self, data: DTOModelType) -> DTOModelType:
        """Add a new entity to the repository."""
        pass

    @abstractmethod
    async def update(self, data: DTOModelType) -> DTOModelType:
        """Update an existing entity in the repository."""
        pass

    @abstractmethod
    async def delete(self, _id: str) -> None:
        """Remove an entity from the repository by their unique identifier."""
        pass

    @abstractmethod
    async def find_by_id(self, _id: str) -> DTOModelType | None:
        """Retrieve a entity by their unique identifier."""
        pass

    @abstractmethod
    async def list_all(self, *filter, offset: int = 0, limit: int = 100, **filter_by) -> list[DTOModelType]:
        """List all entities in the repository."""
        pass
