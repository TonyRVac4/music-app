import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status, BackgroundTasks

from api.src.domain.users.schemas import (
    UserUpdateRequest,
    UserCreateRequest,
    UserDTO,
    UserDataResponse,
)
from api.src.domain.dependencies import get_current_active_user
from api.src.domain.users.exceptions import HTTPExceptionUserNotFound
from api.src.domain.auth.exceptions import HTTPExceptionNoPermission
from api.src.infrastructure.database.enums import Roles
from api.src.domain.auth.utils import check_permissions
from api.src.infrastructure.app import app

logger = logging.getLogger("my_app")

router = APIRouter(prefix="/users", tags=["User"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=UserDataResponse,
)
async def create_user(
    new_user: UserCreateRequest,
        # bt: BackgroundTasks,
) -> UserDTO:
    new_user = await app.user_service.create(new_user)
    # await app.auth_service.send_verification_code(new_user.email, bt)

    return new_user


@router.get(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=UserDataResponse,
)
async def get_user(
    user_id: str,
    current_user: Annotated[UserDTO, Depends(get_current_active_user)],
) -> UserDTO:
    target_user = await app.user_service.get_by_id(user_id)
    if not target_user:
        raise HTTPExceptionUserNotFound
    if not check_permissions(current_user, target_user):
        raise HTTPExceptionNoPermission

    return target_user


@router.put(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_user(
    user_id: str,
    data: UserUpdateRequest,
    current_user: Annotated[UserDTO, Depends(get_current_active_user)],
) -> None:
    target_user = await app.user_service.get_by_id(user_id)

    if not target_user:
        raise HTTPExceptionUserNotFound
    if not check_permissions(current_user, target_user):
        raise HTTPExceptionNoPermission
    if (
        data.role
        and data.role != target_user.role
        and current_user.role != Roles.SUPER_ADMIN
    ):
        # только суперадмин может изменять роль пользователей
        logger.info(
            "User:\n"
            f"'{current_user.role}:{current_user.username}:{current_user.id}:' "
            f"tried to update user role for "
            f"'{target_user.role}:{target_user.username}:{target_user.id}'!\n"
            f"Values: {data.model_dump(exclude_none=True)}"
        )
        raise HTTPExceptionNoPermission

    if (
        data.is_active is not None
        and (
            current_user.role == Roles.USER
            or (current_user.role in (Roles.ADMIN, Roles.SUPER_ADMIN)
             and current_user.id == target_user.id)
        )
    ):
        # только админ+ может изменять is_active пользователей
        raise HTTPExceptionNoPermission

    if (
        data.is_email_verified is not None
        and (
            current_user.role == Roles.USER
            or (current_user.role in (Roles.ADMIN, Roles.SUPER_ADMIN)
             and current_user.id == target_user.id)
        )
    ):
        # только админ+ может изменять is_email_verified пользователей
        raise HTTPExceptionNoPermission

    await app.user_service.update(
        user_id=str(target_user.id),
        data=data,
    )

    logger.info(
        f"User:\n"
        f"'{current_user.role}:{current_user.username}:{current_user.id}' updated profile of "
        f"'{target_user.role}:{target_user.username}:{target_user.id}'!"
    )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
    user_id: str,
    user: Annotated[UserDTO, Depends(get_current_active_user)],
) -> None:
    target_user = await app.user_service.get_by_id(user_id)
    if not target_user:
        raise HTTPExceptionUserNotFound
    if (
        not check_permissions(user, target_user)
        or (target_user.role in (Roles.ADMIN, Roles.SUPER_ADMIN) and target_user.id == user.id)
    ):
        raise HTTPExceptionNoPermission

    await app.user_service.delete(user_id=str(target_user.id))
    await app.auth_service.delete_all_refresh_tokens_by_user_id(user_id=str(target_user.id))
    logger.info(
        f"User:\n"
        f"'{user.role}:{user.username}:{user.id}' deleted profile of "
        f"'{target_user.role}:{target_user.username}:{target_user.id}'!"
    )
