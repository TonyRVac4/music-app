import logging
from typing import AsyncGenerator

from uuid import uuid4
from datetime import datetime
from sqlalchemy import or_
from redis.asyncio import Redis

from .models import SQLAlchemyUserModel
from .schemas import UserCreateRequest, BaseUserInfo, UserDTO, UserUpdateRequest
from .utils import get_password_hash, verify_password_hash, create_jwt, send_email
from .exceptions import (HTTPExceptionInactiveUser, HTTPExceptionInvalidLoginCredentials,
                         HTTPExceptionUserAlreadyExists, HTTPExceptionInvalidEmailVerification,
                         HTTPExceptionEmailNotFound, HTTPExceptionEmailAlreadyVerified,
                         HTTPExceptionUserNotFound, HTTPExceptionInvalidToken)
from api.src.infrastructure.app import app
from api.src.infrastructure.dal.uow import AbstractUnitOfWork
from api.src.infrastructure.dal.datasource import AbstractUnitDataSource

logger = logging.getLogger("my_app")


class AuthService:
    def __init__(
            self,
            unit_of_work: AbstractUnitOfWork[AbstractUnitDataSource],
            redis_client: AsyncGenerator[Redis] = app.async_redis_client,
    ):
        self.uow = unit_of_work
        self._redis_client = redis_client

    async def authenticate_user(self, email, password) -> BaseUserInfo:
        async with self.uow.execute() as datasource:
            user = await datasource.users.find_by_id(
                or_(
                    SQLAlchemyUserModel.username == email,
                    SQLAlchemyUserModel.email == email,
                )
            )
        if not user:
            logger.warning(f"Authentication: Invalid login! '{email}' does not exist!")
            raise HTTPExceptionInvalidLoginCredentials
        if not verify_password_hash(password, user.password):
            logger.warning(f"Authentication: Invalid password! | '{email}'")
            raise HTTPExceptionInvalidLoginCredentials
        if not user.is_active:
            logger.warning(f"Authentication: Inactive account! | '{email}'")
            raise HTTPExceptionInactiveUser
        if not user.is_email_verified:
            logger.warning(f"Authentication: Email is not verified! | '{email}'")
            raise HTTPExceptionInactiveUser

        return BaseUserInfo.model_validate(user)

    @staticmethod
    async def create_access_token(
            sub: str,
            expires_in_min: int = app.settings.auth.access_token_expires_min,
            token_type: str = app.settings.auth.access_token_name,
    ) -> str:
        payload = {
            "sub": str(sub),
        }
        return create_jwt(payload, token_type, expires_in_min)

    @staticmethod
    async def create_refresh_token(
            sub: str,
            expires_in_min: int = app.settings.auth.refresh_token_expires_min,
            token_type: str = app.settings.auth.refresh_token_name,
    ) -> str:
        payload = {
            "sub": str(sub),
        }
        return create_jwt(payload, token_type, expires_in_min)

    async def send_verification_code(self, email: str, background_task) -> None:
        code = str(uuid4())
        async with self._redis_client as client:
            await client.set(email, code, ex=600)

        url = app.settings.app.get_verification_link(email, code)
        background_task.add_task(send_email, email, url)
        logger.info(f"Email verification: Code sent! Email: '{email}'")

    async def confirm_verification_code(self, email: str, code: str) -> None:
        async with self._redis_client as client:
            redis_code = await client.get(email)

        if not redis_code or code != redis_code:
            logger.warning(f"Email verification: Invalid verification code! | '{email}'")
            raise HTTPExceptionInvalidEmailVerification

        async with self.uow.begin() as datasource:
            user = await datasource.users.find_by(email=email)
            user.is_email_verified = True
            await datasource.users.update(user)

        async with self._redis_client as client:
            await client.delete(email)

        logger.info(f"Email verification: Code confirmed, account activated. | '{email}'")

    async def check_refresh_token_exist(self, user_id: str, jti: str) -> None:
        async with self._redis_client as client:
            if await client.zscore(user_id, jti) is None:
                logger.warning(
                    f"Authorization: "
                    f"Refresh token is valid but not in user active tokens!\n"
                    f"User: '{user_id}', JTI: '{jti}'"
                )
                raise HTTPExceptionInvalidToken

    async def add_refresh_token(self, user_id: str, jti: str, exp_data_stamp: int, limit: int = 5):
        await self.delete_expired_refresh_tokens(user_id)

        async with self._redis_client as client:
            await client.zadd(user_id, {jti: exp_data_stamp})

            # узнаём длину отсортированного множества
            refresh_token_num: int = await client.zcard(user_id)
            if refresh_token_num > limit:
                # Удаляем самый старый элемент по позиции (с наименьшим score)
                await client.zremrangebyrank(user_id, 0, 0)

    async def delete_refresh_token(self, user_id: str, jti: str) -> None:
        async with self._redis_client as client:
            await client.zrem(user_id, jti)

    async def delete_expired_refresh_tokens(self, user_id: str) -> None:
        now = round(datetime.now().timestamp())
        async with self._redis_client as client:
            await client.zremrangebyscore(user_id, 0, now)

    async def delete_all_refresh_tokens_by_user_id(self, user_id: str) -> None:
        async with self._redis_client as client:
            await client.delete(user_id)


class UserService:
    def __init__(
            self,
            unit_of_work: AbstractUnitOfWork[AbstractUnitDataSource],
    ):
        self.uow = unit_of_work

    async def create(self, user: UserCreateRequest) -> UserDTO:
        async with self.uow.begin() as datasource:
            #todo возможно нет необходимости в проверке, взамен использовать обработку исключений
            check_user = await datasource.users.find_by(
                or_(
                    SQLAlchemyUserModel.username == user.username,
                    SQLAlchemyUserModel.email == user.email,
                )
            )
            if check_user:
                logger.info(f"Registration: {check_user.username} or {check_user.email} already exist!")
                raise HTTPExceptionUserAlreadyExists

            new_user = UserDTO(
                username=user.username,
                email=str(user.email),
                password=get_password_hash(user.password),
            )
            result: UserDTO = await datasource.users.create(data=new_user)
            logger.info(f"Registration: Account created!\nUsername:{user.username} | Email:{user.email}")
            return result

    async def get_by_id(self, user_id: str) -> UserDTO:
        async with self.uow.execute() as datasource:
            user = await datasource.users.find_by_id(_id=user_id)
            if not user:
                logger.info(f"User with id: '{user_id}' does not exist!")
                raise HTTPExceptionUserNotFound
            return user

    async def check_user_exist_by_email_and_is_not_verified(self, email: str) -> None:
        async with self.uow.execute() as datasource:
            user = await datasource.users.find_by(email=email)

        if not user:
            logger.info(f"User with email: '{email}' does not exist!")
            raise HTTPExceptionEmailNotFound
        if user.is_email_verified:
            logger.info(f"User with email: '{email}' is already verified!")
            raise HTTPExceptionEmailAlreadyVerified

    async def is_user_active(self, user_id: str) -> bool:
        user = await self.get_by_id(user_id)
        if not user.is_active:
            return False
        return True

    async def update(self, user_id: str, data: UserUpdateRequest) -> None:
        data.id = user_id

        if data.email:
            data.is_email_verified = False
        if data.password:
            data.password = get_password_hash(data.password)
        try:
            async with self.uow.begin() as datasource:
                await datasource.users.update(UserDTO.model_validate(data))
        except ValueError:
            raise HTTPExceptionUserNotFound
        #todo нужно написать оброботку нарущения unique constraint
        # except ValueError:
        #     raise HTTPExceptionUserNotFound

    async def delete(self, user_id: str) -> None:
        async with self.uow.begin() as datasource:
            await datasource.users.delete(user_id)
