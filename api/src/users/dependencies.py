from typing import Annotated
import logging

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError
from redis.asyncio import Redis

from .repository import UserRepository
from .services import AuthService, UserService
from .utils import decode_jwt, validate_token_type
from .schemas import TokenData, BaseUserInfo
from .exceptions import HTTPExceptionInvalidToken

from api.src.config import settings
from api.src.dependencies.db_deps import get_async_session_with_commit, get_async_redis_client

logger = logging.getLogger("my_app")


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
    except JWTError as exp:
        logger.warning(f"Authorization: Invalid token: {exp}")
        raise HTTPExceptionInvalidToken
    return TokenData.model_validate(payload)


async def get_current_refresh_token_payload(
        payload: Annotated[TokenData, Depends(get_current_token_payload)],
        auth_service: Annotated[AuthService, Depends(get_auth_service_dependency)],
) -> TokenData:
    if not validate_token_type(payload.type, settings.REFRESH_TOKEN_NAME):
        logger.warning(
            f"Authorization: "
            f"Invalid token type {payload.type}! "
            f"Must be {settings.REFRESH_TOKEN_NAME}!"
            f"User: '{payload.sub}'"
        )
        raise HTTPExceptionInvalidToken

    await auth_service.check_refresh_token_exist(user_id=payload.sub, jti=payload.jti)
    return payload


def get_auth_dependency_from_token_type(token_type: str) -> callable:
    async def get_current_auth_user_from_token(
            payload: Annotated[TokenData, Depends(get_current_token_payload)],
            user_service: Annotated[UserService, Depends(get_user_service_dependency)],
            auth_service: Annotated[AuthService, Depends(get_auth_service_dependency)],
    ) -> BaseUserInfo:
        # проверка типа чтобы нельзя было логинится по refresh и выпускать новые токены по access
        if not validate_token_type(token_type=payload.type, target_type=token_type):
            logger.warning(
                f"Authorization: "
                f"Invalid token type {payload.type}! "
                f"Must be {token_type}! "
                f"User: '{payload.sub}'"
            )
            raise HTTPExceptionInvalidToken
        # если token - refresh проверяет есть ли он в активных токенах пользователя
        if payload.type == settings.REFRESH_TOKEN_NAME:
            await auth_service.check_refresh_token_exist(
                user_id=payload.sub, jti=payload.jti,
            )

        return await user_service.get_user_by_id(user_id=payload.sub)

    return get_current_auth_user_from_token


get_current_auth_user_by_access = get_auth_dependency_from_token_type(settings.ACCESS_TOKEN_NAME)
get_current_auth_user_by_refresh = get_auth_dependency_from_token_type(settings.REFRESH_TOKEN_NAME)
