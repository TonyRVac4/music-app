import logging

from uuid import uuid4
from datetime import datetime
from sqlalchemy import or_
from redis.asyncio import Redis

from .models import SQLAlchemyUserModel
from .repository import UserSQLAlchemyRepository
from .schemas import UserCreateRequest, BaseUserInfo, UserDTO, UserUpdateRequest
from .utils import get_password_hash, verify_password_hash, create_jwt, send_email
from .exceptions import (HTTPExceptionInactiveUser, HTTPExceptionInvalidLoginCredentials,
                         HTTPExceptionUserAlreadyExists, HTTPExceptionInvalidEmailVerification,
                         HTTPExceptionEmailNotFound, HTTPExceptionEmailAlreadyVerified,
                         HTTPExceptionUserNotFound, HTTPExceptionInvalidToken)
from api.src.infrastructure.settings import settings
from api.src.infrastructure.database.repository import AbstractSQLAlchemyRepository

logger = logging.getLogger("my_app")


class AuthService:
    def __init__(self, repository: UserSQLAlchemyRepository, redis_client: Redis):
        self._repository = repository
        self._model = repository.model
        self._redis_client = redis_client

    async def authenticate_user(self, email, password) -> BaseUserInfo:
        user = await self._repository.find_by_id(
            or_(
                self._model.username == email,
                self._model.email == email,
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
    async def create_access_token(sub: str, expires_in_min: int = settings.auth.access_token_expires_min) -> str:
        payload = {
            "sub": str(sub),
        }
        return create_jwt(payload, settings.auth.access_token_name, expires_in_min)

    @staticmethod
    async def create_refresh_token(sub: str, expires_in_min: int = settings.auth.refresh_token_expires_min) -> str:
        payload = {
            "sub": str(sub),
        }
        return create_jwt(payload, settings.auth.refresh_token_name, expires_in_min)

    async def send_verification_code(self, email: str, background_task) -> None:
        code = str(uuid4())
        await self._redis_client.set(email, code, ex=600)

        url = settings.app.get_verification_link(email, code)
        background_task.add_task(send_email, email, url)
        logger.info(f"Email verification: Code sent! Email: '{email}'")

    async def confirm_verification_code(self, email: str, code: str) -> None:
        redis_code = await self._redis_client.get(email)
        if not redis_code or code != redis_code:
            logger.warning(f"Email verification: Invalid verification code! | '{email}'")
            raise HTTPExceptionInvalidEmailVerification

        await self._repository.update(self._model.email == email, is_email_verified=True)
        await self._redis_client.delete(email)
        logger.info(f"Email verification: Code confirmed, account activated. | '{email}'")

    async def check_refresh_token_exist(self, user_id: str, jti: str) -> None:
        if await self._redis_client.zscore(user_id, jti) is None:
            logger.warning(
                f"Authorization: "
                f"Refresh token is valid but not in user active tokens!\n"
                f"User: '{user_id}', JTI: '{jti}'"
            )
            raise HTTPExceptionInvalidToken

    async def add_refresh_token(self, user_id: str, jti: str, exp_data_stamp: int, limit: int = 5):
        await self.delete_expired_refresh_tokens(user_id)
        await self._redis_client.zadd(user_id, {jti: exp_data_stamp})

        # узнаём длину отсортированного множества
        refresh_token_num: int = await self._redis_client.zcard(user_id)
        if refresh_token_num > limit:
            # Удаляем самый старый элемент по позиции (с наименьшим score)
            await self._redis_client.zremrangebyrank(user_id, 0, 0)

    async def delete_refresh_token(self, user_id: str, jti: str) -> None:
        await self._redis_client.zrem(user_id, jti)

    async def delete_expired_refresh_tokens(self, user_id: str) -> None:
        now = round(datetime.now().timestamp())
        await self._redis_client.zremrangebyscore(user_id, 0, now)

    async def delete_all_refresh_tokens_by_user_id(self, user_id: str) -> None:
        await self._redis_client.delete(user_id)


class UserService:
    def __init__(self, repository: AbstractSQLAlchemyRepository):
        self._repository = repository

    async def create(self, user: UserCreateRequest) -> UserDTO:
        user_exist = await self._repository.find_by(
            or_(
                SQLAlchemyUserModel.username == user.username,
                SQLAlchemyUserModel.email == user.email,
            )
        )
        if user_exist:
            logger.info(f"Registration: {user.username} or {user.email} already exist!")
            raise HTTPExceptionUserAlreadyExists

        new_user = UserDTO(
            username=user.username,
            email=str(user.email),
            password=get_password_hash(user.password),
        )
        result: UserDTO = await self._repository.create(data=new_user)
        logger.info(f"Registration: Account created!\nUsername:{user.username} | Email:{user.email}")
        return result

    async def get_by_id(self, user_id: str) -> UserDTO:
        user = await self._repository.find_by_id(_id=user_id)
        if not user:
            logger.info(f"User with id: '{user_id}' does not exist!")
            raise HTTPExceptionUserNotFound
        return user

    async def check_user_exist_by_email_and_is_not_verified(self, email: str) -> None:
        user = await self._repository.find_by(email=email)
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
            await self._repository.update(UserDTO.model_validate(data))
        except ValueError:
            raise HTTPExceptionUserNotFound
        #todo нужно написать оброботку нарущения unique constraint
        # except ValueError:
        #     raise HTTPExceptionUserNotFound

    async def delete(self, user_id: str) -> None:
        await self._repository.delete(user_id)
