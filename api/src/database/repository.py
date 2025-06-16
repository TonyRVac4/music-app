from sqlalchemy import select, insert, update, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from typing import TypeVar, Generic, Type

from .models import Base


ModelType = TypeVar("ModelType", bound=Base)


class SQLAlchemyRepository(Generic[ModelType]):
    model = None

    def __init__(self, session: AsyncSession):
        self._session = session

        if self.model is None:
            raise ValueError("Class attr 'model' is None! Must be an ORM model!")

    async def find_one_or_none(self, *filter, **filter_by) -> ModelType | None:
        try:
            stmt = select(self.model).filter(*filter).filter_by(**filter_by)
            result = await self._session.execute(stmt)
            return result.scalars().one_or_none()
        except SQLAlchemyError as exp:
            # log
            raise

    async def find_all(self, *filter, offset: int = 0, limit: int = 100, **filter_by):
        try:
            stmt = select(self.model).filter(*filter).filter_by(**filter_by).offset(offset).limit(limit)
            result = await self._session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as exp:
            # log
            raise

    async def insert(self, data: dict):
        try:
            stmt = insert(self.model).values(**data).returning(self.model)
            result = await self._session.execute(stmt)
            await self._session.commit()
            return result.scalars().one()
        except SQLAlchemyError as exp:
            # log
            raise

    async def insert_bulk(self, data: list[dict]):
        try:
            stmt = insert(self.model).returning(self.model)
            result = await self._session.execute(
                stmt, data,
            )
            await self._session.commit()
            return result.scalars().all()
        except SQLAlchemyError as exp:
            # log
            raise

    async def update(self, *where, new_obj: dict):
        try:
            stmt = (
                update(self.model)
                .where(*where)
                .values(**new_obj)
                .returning(self.model)
            )
            result = await self._session.execute(stmt)
            await self._session.commit()
            return result.scalars().all()
        except SQLAlchemyError as exp:
            # log
            raise

    async def update_bulk(self, *where, data: list[dict]):
        try:
            stmt = (
                update(self.model)
                .where(*where)
                .returning(self.model)
            )
            result = await self._session.execute(
                stmt, data,
            )
            await self._session.commit()
            return result.scalars().all()
        except SQLAlchemyError as exp:
            # log
            raise

    async def delete(self, *filter, **filter_by):
        try:
            stmt = (
                delete(self.model)
                .filter(*filter)
                .filter_by(**filter_by)
                .returning(self.model)
            )
            result = await self._session.execute(stmt)
            await self._session.commit()
            return result.scalars().all()
        except SQLAlchemyError as exp:
            # log
            raise
