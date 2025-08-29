import logging
import datetime
from math import ceil
from typing import Annotated

from fastapi import APIRouter, Depends, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm

from api.src.domain.auth.schemas import TokenInfoResponse, TokenDTO
from api.src.domain.auth.dependencies import (
    get_current_refresh_token_payload,
    get_current_auth_user_by_access,
)
from api.src.domain.auth.utils import decode_jwt, check_permissions
from api.src.domain.users.schemas import UserDTO
from api.src.domain.auth.exceptions import HTTPExceptionInactiveUser, HTTPExceptionNoPermission

from api.src.infrastructure.app import app

logger = logging.getLogger("my_app")

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=TokenInfoResponse,
)
async def login(
    credentials: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> dict[str, str]:
    user = await app.auth_service.authenticate_user(
        credentials.username, credentials.password
    )

    access_token: str = await app.auth_service.create_access_token(str(user.id))
    refresh_token: str = await app.auth_service.create_refresh_token(str(user.id))

    refresh_token_decoded: dict = decode_jwt(refresh_token)
    await app.auth_service.save_refresh_token(
        user_id=refresh_token_decoded["sub"],
        jti=refresh_token_decoded["jti"],
        exp_date_stamp=refresh_token_decoded["exp"],
    )

    logger.info(f"Authorization: User '{user.id}' created a new pair of tokens.")
    logger.info(f"Authentication: User '{user.id}' logged in!")

    return {"access_token": access_token, "refresh_token": refresh_token}


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Logs out user using refresh token.",
)
async def logout(
    payload: Annotated[TokenDTO, Depends(get_current_refresh_token_payload)],
) -> None:
    await app.auth_service.delete_refresh_token(
        jti=payload.jti,
    )
    logger.info(f"Authentication: User '{payload.sub}' logged out!")


@router.post(
    "/refresh-token",
    status_code=status.HTTP_200_OK,
    response_model=TokenInfoResponse,
    description="Refreshes tokens using refresh token.",
)
async def refresh_token(
    payload: Annotated[TokenDTO, Depends(get_current_refresh_token_payload)],
) -> dict[str, str]:
    if not await app.user_service.is_user_active(payload.sub):
        raise HTTPExceptionInactiveUser

    # await app.auth_service.delete_expired_refresh_tokens()

    access_token: str = await app.auth_service.create_access_token(payload.sub)
    # время инвалидации refresh остается прежним (пользователь должен будет снова залогинится через 30 дней)
    # с каждым refresh время может немного увеличиваться из-за ceil
    refresh_token: str = await app.auth_service.create_refresh_token(
        sub=payload.sub,
        expires_in_min=ceil((payload.exp - datetime.datetime.now().timestamp()) / 60),
    )
    await app.auth_service.delete_refresh_token(jti=payload.jti)
    await app.auth_service.save_refresh_token(
        user_id=payload.sub,
        jti=decode_jwt(refresh_token)["jti"],
        exp_date_stamp=payload.exp,
    )

    logger.info(f"Authorization: User '{payload.sub}' created a new pair of tokens.")

    return {"access_token": access_token, "refresh_token": refresh_token}


@router.post(
    "/terminate-all-sessions/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Logs out user from all devices using access token. Can be used by admins.",
)
async def terminate_all_sessions(
    user_id: str,
    current_user: Annotated[UserDTO, Depends(get_current_auth_user_by_access)],
) -> None:
    target_user: UserDTO = await app.user_service.get_by_id(user_id=user_id)
    if not check_permissions(current_user, target_user):
        raise HTTPExceptionNoPermission
    await app.auth_service.delete_all_refresh_tokens_by_user_id(user_id)

    logger.info(
        f"Removed all active refresh tokens:\n"
        f"'{current_user.role}:{current_user.username}:{current_user.id}:' "
        f"from "
        f"'{target_user.role}:{target_user.username}:{target_user.id}'"
    )


@router.post(
    "/send-email-verification-code",
    status_code=status.HTTP_202_ACCEPTED,
)
async def send_email_verification_code(
    email: str,
    background_tasks: BackgroundTasks,
) -> None:
    await app.user_service.check_user_exist_by_email_and_is_not_verified(email=email)
    await app.auth_service.send_verification_code(email, background_tasks)


@router.get(
    "/verify-email",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def verify_email(
    email: str,
    code: str,
) -> None:
    await app.user_service.check_user_exist_by_email_and_is_not_verified(email=email)
    await app.auth_service.confirm_verification_code(email=email, code=code)
