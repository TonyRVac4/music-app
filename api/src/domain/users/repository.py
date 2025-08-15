import logging
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import select, insert, update, delete

from api.src.infrastructure.database.repository import AbstractSQLAlchemyRepository
from api.src.domain.users.models import SQLAlchemyUserModel
from .schemas import UserDTO

logger = logging.getLogger("my_app")


class UserSQLAlchemyRepository(AbstractSQLAlchemyRepository):
    async def find_by_id(self, _id: str) -> UserDTO | None:
        try:
            user = await self._session.get(SQLAlchemyUserModel, _id)
            if user:
                return UserDTO.model_validate(user)
            return None
        except SQLAlchemyError as exp:
            logger.error(f"SQLAlchemyError: {exp}")
            raise

    async def find_by(self, *filter_, **filter_by_) -> UserDTO | None:
        stmt = select(SQLAlchemyUserModel).filter(*filter_).filter_by(**filter_by_)
        try:
            result = await self._session.execute(stmt)
            user = result.scalar_one_or_none()
        except SQLAlchemyError as exp:
            logger.error(f"SQLAlchemyError: {exp}")
            raise
        else:
            if user:
                return UserDTO.model_validate(user)
            return None

    async def list_all(self, *filter, offset: int = 0, limit: int = 100, **filter_by) -> list[UserDTO]:
        try:
            stmt = (
                select(SQLAlchemyUserModel).
                filter(*filter).
                filter_by(**filter_by).
                offset(offset).
                limit(limit)
            )
            result = await self._session.execute(stmt)
            return [UserDTO.model_validate(user) for user in result.scalars().all()]
        except SQLAlchemyError as exp:
            logger.error(f"SQLAlchemyError: {exp}")
            raise

    async def create(self, data: UserDTO) -> UserDTO:
        if not data.id:
            data.id = uuid4()

        stmt = insert(SQLAlchemyUserModel).values(**data)

        try:
            result = await self._session.execute(stmt)
            await self._session.flush()
        except IntegrityError as exp:
            logger.error(f"IntegrityError: {exp}")
            raise # custom exception
        except SQLAlchemyError as exp:
            logger.error(f"SQLAlchemyError: {exp}")
            raise
        else:
            return result.scalars().one()

    async def update(self, data: UserDTO) -> UserDTO:
        stmt = (
            update(SQLAlchemyUserModel)
            .where(SQLAlchemyUserModel.id == data.id)
            .values(
                username=data.username,
                email=data.email,
                password=data.password,
                is_active=data.is_active,
                is_email_verified=data.is_email_verified,
                roles=data.roles,
            )
        )

        try:
            result = await self._session.execute(stmt)
            await self._session.flush()
        except IntegrityError as e:
            #todo нужно написать окастомные искючения нарущения unique constraint
            raise ValueError(f"Unique violation: {e.orig}")
        except SQLAlchemyError as exp:
            logger.error(f"SQLAlchemyError: {exp}")
            raise
        else:
            if result.rowcount == 0:
                raise ValueError(f"User with id {data.id} does not exist")
            return result.scalars().one()


    async def delete(self, _id) -> None:
        try:
            await self._session.execute(
                delete(SQLAlchemyUserModel).where(SQLAlchemyUserModel.id == _id)
            )
            await self._session.flush()
        except SQLAlchemyError as exp:
            logger.error(f"SQLAlchemyError: {exp}")
            raise
