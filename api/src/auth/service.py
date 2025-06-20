from uuid import uuid4
from datetime import datetime
from sqlalchemy import or_
from redis.asyncio import Redis

from .repository import UserRepository
from .schemas import UserCreate, BaseUserInfo
from .utils import get_password_hash, verify_password_hash, create_jwt, send_email
from .exceptions import (HTTPExceptionInactiveUser, HTTPExceptionInvalidLoginCredentials,
                         HTTPExceptionUserAlreadyExists, HTTPExceptionInvalidEmailVerification,
                         HTTPExceptionEmailNotFound, HTTPExceptionEmailAlreadyVerified, HTTPExceptionUserNotFound)

from api.src.config import settings


class AuthService:
    def __init__(self, repository: UserRepository, redis_client: Redis):
        self._repository = repository
        self._model = repository.model
        self._redis_client = redis_client

    async def authenticate_user(self, email, password) -> BaseUserInfo:
        user = await self._repository.find_one_or_none(
            or_(
                self._model.username == email,
                self._model.email == email,
            )
        )
        if not user:
            raise HTTPExceptionInvalidLoginCredentials
        if not verify_password_hash(password, user.password):
            raise HTTPExceptionInvalidLoginCredentials
        if not user.is_active or not user.is_email_verified:
            raise HTTPExceptionInactiveUser

        return BaseUserInfo.model_validate(user)

    @staticmethod
    async def create_access_token(sub: str, expires_in_min: int = settings.ACCESS_TOKEN_EXPIRES_MIN) -> str:
        payload = {
            "sub": str(sub),
        }
        return create_jwt(payload, settings.ACCESS_TOKEN_NAME, expires_in_min)

    @staticmethod
    async def create_refresh_token(sub: str, expires_in_min: int = settings.REFRESH_TOKEN_EXPIRES_MIN) -> str:
        payload = {
            "sub": str(sub),
        }
        return create_jwt(payload, settings.REFRESH_TOKEN_NAME, expires_in_min)

    async def send_verification_code(self, email: str, background_task) -> None:
        code = str(uuid4())
        await self._redis_client.set(email, code, ex=600)

        url = settings.get_verification_link(email, code)
        background_task.add_task(send_email, email, url)

    async def confirm_verification_code(self, email: str, code: str) -> None:
        redis_code = await self._redis_client.get(email)
        if not redis_code or code != redis_code:
            raise HTTPExceptionInvalidEmailVerification

        await self._repository.update(self._model.email == email, is_email_verified=True)
        await self._redis_client.delete(email)

    async def check_refresh_token_exist(self, user_id: str, jti: str) -> bool:
        if await self._redis_client.zscore(user_id, jti) is not None:
            return True
        return False

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
    def __init__(self, repository: UserRepository):
        self._repository = repository
        self._model = repository.model

    async def register_new_user(self, user: UserCreate) -> BaseUserInfo:
        user_exist = await self._repository.find_one_or_none(
            or_(
                self._model.username == user.username,
                self._model.email == user.email,
            )
        )
        if user_exist:
            raise HTTPExceptionUserAlreadyExists

        user_data = user.model_dump()
        user_data["password"] = get_password_hash(password=user.password)
        user_data["id"] = uuid4()
        result = await self._repository.insert(data=user_data)
        return BaseUserInfo.model_validate(result)

    async def get_user_by_id(self, user_id: str) -> BaseUserInfo:
        user = await self._repository.find_one_or_none(id=user_id)
        if not user:
            raise HTTPExceptionUserNotFound
        return BaseUserInfo.model_validate(user)

    async def check_user_exist_by_email_and_is_not_verified(self, email: str) -> None:
        user = await self._repository.find_one_or_none(email=email)
        if not user:
            raise HTTPExceptionEmailNotFound
        if user.is_email_verified:
            raise HTTPExceptionEmailAlreadyVerified

    async def check_user_is_active(self, user_id: str) -> None:
        user: BaseUserInfo = await self.get_user_by_id(user_id)
        if not user.is_active:
            raise HTTPExceptionInactiveUser
