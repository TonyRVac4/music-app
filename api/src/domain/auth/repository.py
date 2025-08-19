import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update

from api.src.infrastructure.database.repository import AbstractSQLAlchemyRepository
from api.src.infrastructure.database.exceptions import (
    EntityNotFound,
    ConstraintViolation,
)
from .models import SQLAlchemyRefreshTokenModel
from .schemas import RefreshTokenDTO


logger = logging.getLogger("my_app")


class SQLAlchemyRefreshTokenRepository(AbstractSQLAlchemyRepository):
    def __init__(self, session: AsyncSession):
        self._session = session
        self._model = SQLAlchemyRefreshTokenModel

    async def find_by_id(self, _id: int) -> RefreshTokenDTO | None:
        token = await self._session.get(self._model, _id)

        if not token:
            return None
        return RefreshTokenDTO.model_validate(token)

    async def find_by(self, *filter_, **filter_by_) -> RefreshTokenDTO | None:
        stmt = select(self._model).filter(*filter_).filter_by(**filter_by_)

        result = await self._session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            return RefreshTokenDTO.model_validate(user)
        return None

    async def list_all(
        self, *filter, offset: int = 0, limit: int = 100, **filter_by
    ) -> list[RefreshTokenDTO]:
        stmt = (
            select(self._model)
            .filter(*filter)
            .filter_by(**filter_by)
            .offset(offset)
            .limit(limit)
        )

        result = await self._session.execute(stmt)
        return [
            RefreshTokenDTO.model_validate(token) for token in result.scalars().all()
        ]

    async def create(self, data: RefreshTokenDTO) -> RefreshTokenDTO:
        stmt = (
            insert(self._model)
            .values(**data.model_dump(exclude_none=True))
            .returning(self._model)
        )
        try:
            result = await self._session.execute(stmt)
            await self._session.flush()
        except IntegrityError as exp:
            logger.error(f"SQLAlchemyError IntegrityError: {str(exp)}")
            raise ConstraintViolation(f"Constraint violation: {str(exp)}")

        return RefreshTokenDTO.model_validate(result.scalars().one())

    async def update(self, _id: str, data: RefreshTokenDTO) -> RefreshTokenDTO:
        user = await self._session.get(self._model, _id)
        if not user:
            raise EntityNotFound(f"Token {_id} not found!")

        stmt = (
            update(self._model)
            .where(self._model.id == _id)
            .values(**data.model_dump(exclude_none=True))
            .returning(self._model)
        )
        try:
            result = await self._session.execute(stmt)
            await self._session.flush()
        except IntegrityError as exp:
            logger.error(f"SQLAlchemyError IntegrityError: {str(exp)}")
            raise ConstraintViolation(f"Constraint violation: {str(exp)}")

        return RefreshTokenDTO.model_validate(result.scalars().one())

    async def delete(self, _id: int) -> None:
        token = await self._session.get(self._model, _id)
        if not token:
            raise EntityNotFound(f"Token {_id} not found!")

        try:
            await self._session.delete(token)
            await self._session.flush()
        except IntegrityError as exp:
            logger.error(f"SQLAlchemyError IntegrityError: {str(exp)}")
            raise ConstraintViolation(f"Constraint violation: {str(exp)}")
