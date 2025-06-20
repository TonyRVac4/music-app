from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError
from redis.asyncio import Redis

from .repository import UserRepository
from .service import AuthService, UserService
from .utils import decode_jwt, validate_token_type
from .schemas import TokenData, BaseUserInfo
from .exceptions import HTTPExceptionInvalidToken, HTTPExceptionInactiveUser

from api.src.config import settings
from api.src.dependencies.db_dep import get_async_session_with_commit, get_async_redis_client


async def get_auth_service_dependency(
        session: Annotated[AsyncSession, Depends(get_async_session_with_commit)],
        redis_client: Annotated[Redis, Depends(get_async_redis_client)],
) -> AuthService:
    return AuthService(UserRepository(session), redis_client)


async def get_user_service_dependency(session: AsyncSession = Depends(get_async_session_with_commit)) -> UserService:
    return UserService(UserRepository(session))


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_token_payload(token: Annotated[str, Depends(oauth2_scheme)]) -> TokenData:
    try:
        payload: dict = decode_jwt(token)
    except JWTError:
        raise HTTPExceptionInvalidToken
    return TokenData.model_validate(payload)


async def get_current_refresh_token_payload(
        payload: Annotated[TokenData, Depends(get_current_token_payload)],
) -> TokenData:
    if not validate_token_type(payload.type, settings.REFRESH_TOKEN_NAME):
        raise HTTPExceptionInvalidToken
    return payload


def get_auth_dependency_from_token_type(token_type: str) -> callable:
    async def get_current_auth_user_from_token(
            token_payload: Annotated[TokenData, Depends(get_current_token_payload)],
            user_service: Annotated[UserService, Depends(get_user_service_dependency)],
            auth_service: Annotated[AuthService, Depends(get_auth_service_dependency)],
    ) -> BaseUserInfo:
        # проверка типа чтобы нельзя было логинится по refresh и выпускать новые токены по access
        if not validate_token_type(token_type=token_payload.type, target_type=token_type):
            raise HTTPExceptionInvalidToken
        # если token - refresh проверяет есть ли он в активных токенах пользователя
        if token_payload.type == settings.REFRESH_TOKEN_NAME:
            if not await auth_service.check_refresh_token_exist(
                user_id=token_payload.sub, jti=token_payload.jti,
            ):
                raise HTTPExceptionInvalidToken

        return await user_service.get_user_by_id(user_id=token_payload.sub)

    return get_current_auth_user_from_token


get_current_auth_user_by_access = get_auth_dependency_from_token_type(settings.ACCESS_TOKEN_NAME)
get_current_auth_user_by_refresh = get_auth_dependency_from_token_type(settings.REFRESH_TOKEN_NAME)


async def get_current_active_user(
        user: Annotated[BaseUserInfo, Depends(get_current_auth_user_by_access)]
) -> BaseUserInfo:
    if not user.is_active:
        raise HTTPExceptionInactiveUser
    return user
