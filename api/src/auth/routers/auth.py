import logging
import datetime
from math import ceil
from typing import Annotated

from fastapi import APIRouter, Depends, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm

from api.src.auth.schemas import UserCreate, BaseUserInfo, TokenInfoOut, TokenData
from api.src.auth.dependencies import (get_auth_service_dependency, get_user_service_dependency,
                                       get_current_auth_user_by_access, get_current_refresh_token_payload)
from api.src.auth.service import UserService, AuthService
from api.src.auth.utils import decode_jwt, check_permissions


logger = logging.getLogger("my_app")

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=BaseUserInfo,
)
async def register(
        new_user: UserCreate,
        background_tasks: BackgroundTasks,
        user_service: Annotated[UserService, Depends(get_user_service_dependency)],
        auth_service: Annotated[AuthService, Depends(get_auth_service_dependency)],
) -> BaseUserInfo:
    result = await user_service.register_new_user(user=new_user)
    await auth_service.send_verification_code(result.email, background_tasks)
    return result


@router.post(
    "/resend-email-verification-code",
    status_code=status.HTTP_202_ACCEPTED,
)
async def resend_email_verification_code(
        email: str,
        background_tasks: BackgroundTasks,
        user_service: Annotated[UserService, Depends(get_user_service_dependency)],
        auth_service: Annotated[AuthService, Depends(get_auth_service_dependency)],
) -> None:
    await user_service.check_user_exist_by_email_and_is_not_verified(email=email)
    await auth_service.send_verification_code(email, background_tasks)


@router.get(
    "/verify-email",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def verify_email(
        email: str, code: str,
        user_service: Annotated[UserService, Depends(get_user_service_dependency)],
        auth_service: Annotated[AuthService, Depends(get_auth_service_dependency)],
) -> None:
    await user_service.check_user_exist_by_email_and_is_not_verified(email=email)
    await auth_service.confirm_verification_code(email=email, code=code)


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=TokenInfoOut,
)
async def login(
        credentials: Annotated[OAuth2PasswordRequestForm, Depends()],
        auth_service: Annotated[AuthService, Depends(get_auth_service_dependency)],
) -> TokenInfoOut:
    user = await auth_service.authenticate_user(
        credentials.username, credentials.password
    )

    access_token: str = await auth_service.create_access_token(user.id)
    refresh_token: str = await auth_service.create_refresh_token(user.id)

    refresh_token_decoded: dict = decode_jwt(refresh_token)
    await auth_service.add_refresh_token(
        user_id=refresh_token_decoded["sub"],
        jti=refresh_token_decoded["jti"],
        exp_data_stamp=refresh_token_decoded["exp"],
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
        payload: Annotated[TokenData, Depends(get_current_refresh_token_payload)],
        auth_service: Annotated[AuthService, Depends(get_auth_service_dependency)],
) -> None:
    await auth_service.delete_refresh_token(
        user_id=payload.sub, jti=payload.jti,
    )
    logger.info(f"Authentication: User '{payload.sub}' logged out!")


@router.post(
    "/refresh-token",
    status_code=status.HTTP_200_OK,
    response_model=TokenInfoOut,
    description="Refreshes tokens using refresh token.",
)
async def refresh_token(
        payload: Annotated[TokenData, Depends(get_current_refresh_token_payload)],
        auth_service: Annotated[AuthService, Depends(get_auth_service_dependency)],
        user_service: Annotated[UserService, Depends(get_user_service_dependency)],
) -> TokenInfoOut:
    await user_service.check_user_is_active(payload.sub)

    await auth_service.delete_expired_refresh_tokens(user_id=payload.sub)
    await auth_service.check_refresh_token_exist(user_id=payload.sub, jti=payload.jti)

    access_token: str = await auth_service.create_access_token(payload.sub)
    # время инвалидации refresh остается прежним (пользователь должен будет снова залогинится через 30 дней)
    refresh_token: str = await auth_service.create_refresh_token(
        sub=payload.sub,
        expires_in_min=ceil((payload.exp - datetime.datetime.now().timestamp()) / 60),
    )
    await auth_service.delete_refresh_token(
        user_id=payload.sub,
        jti=payload.jti
    )
    await auth_service.add_refresh_token(
        user_id=payload.sub,
        jti=decode_jwt(refresh_token)["jti"],
        exp_data_stamp=payload.exp,
    )

    logger.info(f"Authorization: User '{payload.sub}' created a new pair of tokens.")

    return {"access_token": access_token, "refresh_token": refresh_token}


@router.post(
    "/terminate-all-user-sessions",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Logs out user from all devices using access token. Can be used by admins.",
)
async def terminate_all_user_sessions(
        user_id: str,
        current_user: Annotated[BaseUserInfo, Depends(get_current_auth_user_by_access)],
        auth_service: Annotated[AuthService, Depends(get_auth_service_dependency)],
        user_service: Annotated[UserService, Depends(get_user_service_dependency)],
) -> None:
    target_user: BaseUserInfo = await user_service.get_user_by_id(user_id=user_id)
    check_permissions(current_user, target_user)
    await auth_service.delete_all_refresh_tokens_by_user_id(user_id)

    logger.info(
        f"Removed all active refresh tokens:\n"
        f"'{current_user.role}:{current_user.username}:{current_user.id}:' "
        f"from "
        f"'{target_user.role}:{target_user.username}:{target_user.id}'"
    )
