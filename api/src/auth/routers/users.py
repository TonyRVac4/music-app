import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status, BackgroundTasks

from api.src.auth.schemas import BaseUserInfo, UserUpdate
from api.src.auth.dependencies import (get_auth_service_dependency, get_user_service_dependency,
                                       get_current_active_user)
from api.src.auth.service import UserService, AuthService


logger = logging.getLogger("my_app")

router = APIRouter(prefix="/users", tags=["User"])


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=BaseUserInfo,
)
async def get_self_info(
        user: Annotated[BaseUserInfo, Depends(get_current_active_user)]
) -> BaseUserInfo:
    return user


@router.patch(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=BaseUserInfo,
)
async def update_user(
        data: UserUpdate,
        bt: BackgroundTasks,
        user: Annotated[BaseUserInfo, Depends(get_current_active_user)],
        user_service: Annotated[UserService, Depends(get_user_service_dependency)],
        auth_service: Annotated[AuthService, Depends(get_auth_service_dependency)],
) -> BaseUserInfo:
    updated_user: BaseUserInfo = await user_service.update(
        user_id=user.id, **data.model_dump(exclude_none=True),
    )

    if not updated_user.is_email_verified:
        await auth_service.send_verification_code(
            email=updated_user.email, background_task=bt,
        )

    logger.info(
        f"User:\n"
        f"'{user.role}:{user.username}:{user.id}' updated self profile!"
    )
    return updated_user


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
        user: Annotated[BaseUserInfo, Depends(get_current_active_user)],
        user_service: Annotated[UserService, Depends(get_user_service_dependency)],
) -> None:
    await user_service.delete(user_id=user.id)

    logger.info(
        f"User:\n"
        f"'{user.role}:{user.username}:{user.id}' deleted self account!"
    )
