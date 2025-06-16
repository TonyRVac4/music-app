from uuid import uuid4

from sqlalchemy import or_

from .repository import UserRepository
from .schemas import UserCreate
from .utils import get_password_hash, verify_password_hash, create_jwt
from .exceptions import (HTTPExceptionInactiveUser, HTTPExceptionInvalidLoginCredentials,
                         HTTPExceptionUserAlreadyExists)

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
        if not user.is_active:
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
                UserModel.email == user.email
            )
        )
        if user_exist:
            raise HTTPExceptionUserAlreadyExists

        user_data = user.model_dump()
        user_data["password"] = get_password_hash(password=user.password)
        user_data["id"] = uuid4()
        result = await self._repository.insert(data=user_data)
        return result
