import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status

from api.src.domain.users.schemas import UserUpdateRequest, UserCreateRequest, UserDTO
from api.src.infrastructure.dependencies.auth import get_current_active_user
from api.src.domain.users.exceptions import HTTPExceptionNoPermission, HTTPExceptionUserNotFound
from api.src.infrastructure.database.enums import Roles
from api.src.domain.users.utils import check_permissions
from api.src.infrastructure.app import app

logger = logging.getLogger("my_app")

router = APIRouter(prefix="/users", tags=["User"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=UserDTO,
)
async def create_user(
        new_user: UserCreateRequest,
) -> UserDTO:
    return await app.user_service.create(check_user=new_user)


@router.get(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=UserDTO,
)
async def get_user(
        user_id: str,
        user: Annotated[UserDTO, Depends(get_current_active_user)]
) -> UserDTO:
    if user.id == user_id or user.role in (Roles.ADMIN, Roles.SUPER_ADMIN):
        return user

    raise HTTPExceptionNoPermission


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
        data.role and
        data.role != target_user.role and
        current_user.role != Roles.SUPER_ADMIN
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
        data.is_active and
        data.is_active != target_user.is_active and
        current_user.role in (Roles.ADMIN, Roles.SUPER_ADMIN) and
        current_user.id != target_user.id # админы+ не могут изменять статус у самих себя
    ):
        # только админ+ может изменять статус пользователей
        raise HTTPExceptionNoPermission

    await app.user_service.update(
        user_id=str(current_user.id), data=data,
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
    if not check_permissions(user, target_user):
        raise HTTPExceptionNoPermission

    await app.user_service.delete(user_id=str(user.id))

    logger.info(
        f"User:\n"
        f"'{user.role}:{user.username}:{user.id}' deleted profile of "
        f"'{target_user.role}:{target_user.username}:{target_user.id}'!"
    )
