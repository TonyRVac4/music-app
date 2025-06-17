from uuid import uuid4

from sqlalchemy import or_

from .repository import UserRepository
from .schemas import UserCreate
from .utils import get_password_hash, verify_password_hash, create_jwt, async_redis_client, send_email
from .exceptions import (HTTPExceptionInactiveUser, HTTPExceptionInvalidLoginCredentials,
                         HTTPExceptionUserAlreadyExists, HTTPExceptionInvalidEmailVerification,
                         HTTPExceptionEmailNotFound, HTTPExceptionEmailAlreadyVerified)

from api.src.database.models import UserModel
from api.src.config import settings


class AuthService:
    def __init__(self, repository: UserRepository):
        self._repository = repository

    async def authenticate_user(self, email, password) -> UserModel:
        user = await self._repository.find_one_or_none(
            or_(
                UserModel.username == email,
                UserModel.email == email,
            )
        )
        if not user:
            raise HTTPExceptionInvalidLoginCredentials
        if not verify_password_hash(password, user.password):
            raise HTTPExceptionInvalidLoginCredentials
        if not user.is_active or not user.is_email_verified:
            raise HTTPExceptionInactiveUser

        return user

    @staticmethod
    async def create_access_token(user: UserModel) -> str:
        payload = {
            "sub": str(user.id),
        }
        return create_jwt(payload, settings.ACCESS_TOKEN_NAME, settings.ACCESS_TOKEN_EXPIRES_MIN)

    @staticmethod
    async def create_refresh_token(user: UserModel) -> str:
        payload = {
            "sub": str(user.id),
        }
        return create_jwt(payload, settings.REFRESH_TOKEN_NAME, settings.REFRESH_TOKEN_EXPIRES_MIN)


class UserService:
    def __init__(self, repository: UserRepository):
        self._repository = repository

    async def register_new_user(self, user: UserCreate) -> UserModel:
        user_exist = await self._repository.find_one_or_none(
            or_(
                UserModel.username == user.username,
                UserModel.email == user.email,
            )
        )
        if user_exist:
            raise HTTPExceptionUserAlreadyExists

        user_data = user.model_dump()
        user_data["password"] = get_password_hash(password=user.password)
        user_data["id"] = uuid4()
        result = await self._repository.insert(data=user_data)
        return result

    async def check_user_exist_by_email_and_is_not_verified(self, email: str) -> None:
        user = await self._repository.find_one_or_none(email=email)
        if not user:
            raise HTTPExceptionEmailNotFound
        if user.is_email_verified:
            raise HTTPExceptionEmailAlreadyVerified

    @staticmethod
    async def send_verification_code(email: str, background_task) -> None:
        code = str(uuid4())
        await async_redis_client.set(email, code, ex=600)

        url = "http://{host}:{port}/api/v1/auth/verify_email?email={email}&code={code}".format(
            host=settings.APP_HOST,
            port=settings.APP_PORT,
            email=email,
            code=code,
        )
        background_task.add_task(send_email, email, url)

    async def confirm_verification_code(self, email: str, code: str) -> None:
        redis_code = await async_redis_client.get(email)
        if not redis_code or code != redis_code:
            raise HTTPExceptionInvalidEmailVerification

        await self._repository.update(UserModel.email == email, is_email_verified=True)
        await async_redis_client.delete(email)
