import logging
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from api.src.domain.auth.schemas import TokenDTO
from api.src.domain.auth.utils import decode_jwt, validate_token_type
from api.src.domain.auth.exceptions import HTTPExceptionInvalidToken
from api.src.domain.users.schemas import UserDTO
from api.src.infrastructure.app import app
from api.src.infrastructure.settings import settings


logger = logging.getLogger("my_app")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_token_payload(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> TokenDTO:
    try:
        payload: dict = decode_jwt(token)
    except JWTError as exp:
        logger.warning(f"Authorization: Invalid token: {exp}")
        raise HTTPExceptionInvalidToken
    return TokenDTO.model_validate(payload)


async def get_current_refresh_token_payload(
    payload: Annotated[TokenDTO, Depends(get_current_token_payload)],
) -> TokenDTO:
    if not validate_token_type(payload.type, settings.auth.refresh_token_name):
        logger.warning(
            f"Authorization: "
            f"Invalid token type {payload.type}! "
            f"Must be {settings.auth.refresh_token_name}!"
            f"User: '{payload.sub}'"
        )
        raise HTTPExceptionInvalidToken

    await app.auth_service.check_refresh_token_exist(
        user_id=payload.sub, jti=payload.jti,
    )
    return payload


def get_auth_dependency_from_token_type(token_type: str) -> callable:
    async def get_current_auth_user_from_token(
        payload: Annotated[TokenDTO, Depends(get_current_token_payload)],
    ) -> UserDTO:
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
        if payload.type == settings.auth.refresh_token_name:
            await app.auth_service.check_refresh_token_exist(
                user_id=payload.sub,
                jti=payload.jti,
            )

        return await app.user_service.get_by_id(user_id=payload.sub)

    return get_current_auth_user_from_token


get_current_auth_user_by_access = get_auth_dependency_from_token_type(
    settings.auth.access_token_name
)
get_current_auth_user_by_refresh = get_auth_dependency_from_token_type(
    settings.auth.refresh_token_name
)
