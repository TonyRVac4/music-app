from fastapi import Depends

from .repository import UserRepository
from .service import AuthService, UserService
from api.src.database.db_config import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession


def get_auth_service_dependency(session: AsyncSession = Depends(get_async_session)) -> AuthService:
    return AuthService(UserRepository(session))


def get_user_service_dependency(session: AsyncSession = Depends(get_async_session)) -> UserService:
    return UserService(UserRepository(session))
