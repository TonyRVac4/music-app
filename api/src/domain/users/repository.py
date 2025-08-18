import logging
from uuid import uuid4

from pydantic import UUID4
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import select, insert, update, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession

from api.src.infrastructure.database.repository import AbstractSQLAlchemyRepository
from api.src.domain.users.models import SQLAlchemyUserModel
from api.src.infrastructure.database.exceptions import ConstraintViolation, EntityNotFound
from .schemas import UserDTO

logger = logging.getLogger("my_app")


class SQLAlchemyUserRepository(AbstractSQLAlchemyRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def find_by_id(self, _id: str) -> UserDTO | None:
        user = await self._session.get(SQLAlchemyUserModel, _id)

        if not user:
             return None
        return UserDTO.model_validate(user)

    async def find_by(self, *filter_, **filter_by_) -> UserDTO | None:
        stmt = select(SQLAlchemyUserModel).filter(*filter_).filter_by(**filter_by_)

        result = await self._session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            return UserDTO.model_validate(user)
        return None

    async def list_all(self, *filter, offset: int = 0, limit: int = 100, **filter_by) -> list[UserDTO]:
        stmt = (
            select(SQLAlchemyUserModel).
            filter(*filter).
            filter_by(**filter_by).
            offset(offset).
            limit(limit)
        )

        result = await self._session.execute(stmt)
        return [UserDTO.model_validate(user) for user in result.scalars().all()]

    async def create(self, data: UserDTO) -> UserDTO:
        if not data.id:
            data.id = uuid4()

        stmt = (
            insert(SQLAlchemyUserModel).
            values(**data.model_dump()).
            returning(SQLAlchemyUserModel)
        )
        try:
            result = await self._session.execute(stmt)
            await self._session.flush()
        except IntegrityError as exp:
            logger.error(f"SQLAlchemyError IntegrityError: {str(exp)}")
            raise ConstraintViolation(f"Constraint violation: {str(exp)}")

        return UserDTO.model_validate(result.scalars().one())

    async def update(self, _id: str, data: UserDTO) -> UserDTO:
        user = await self._session.get(SQLAlchemyUserModel, _id)
        if not user:
            raise EntityNotFound(f"User {_id} not found!")

        if (data.email and data.email != user.email) or (data.username and data.username != user.username):
            existing = await self._session.execute(
                select(SQLAlchemyUserModel).where(
                    SQLAlchemyUserModel.id != _id,
                    or_(
                        SQLAlchemyUserModel.email == data.email,
                        SQLAlchemyUserModel.username == data.username
                    ),
                )
            )
            existing_user = existing.scalars()
            if existing_user:
                raise ConstraintViolation("Username or email is already in use")

        data.id = UUID4(_id)
        stmt = (
            update(SQLAlchemyUserModel).
            where(SQLAlchemyUserModel.id == _id).
            values(**data.model_dump(exclude_none=True)).
            returning(SQLAlchemyUserModel)
        )
        try:
            result = await self._session.execute(stmt)
            await self._session.flush()
        except IntegrityError as exp:
            logger.error(f"SQLAlchemyError IntegrityError: {str(exp)}")
            raise ConstraintViolation(f"Constraint violation: {str(exp)}")

        return UserDTO.model_validate(result.scalars().one())

    async def delete(self, _id) -> None:
        user = await self._session.get(SQLAlchemyUserModel, _id)
        if not user:
            raise EntityNotFound(f"User {_id} not found!")

        try:
            await self._session.delete(user)
            await self._session.flush()
        except IntegrityError as exp:
            logger.error(f"SQLAlchemyError IntegrityError: {str(exp)}")
            raise ConstraintViolation(f"Constraint violation: {str(exp)}")
