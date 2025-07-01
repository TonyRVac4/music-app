from typing import Annotated

from fastapi import Depends

from api.src.users.dependencies import get_current_auth_user_by_access, logger
from api.src.users.exceptions import HTTPExceptionInactiveUser, HTTPExceptionNoPermission
from api.src.users.schemas import BaseUserInfo
from api.src.database.enums import Roles


async def get_current_active_user(
        user: Annotated[BaseUserInfo, Depends(get_current_auth_user_by_access)],
) -> BaseUserInfo:
    if not user.is_active:
        logger.info(
            f"Authorization: "
            f"Inactive user {user.id} is trying to get in by access token!"
        )
        raise HTTPExceptionInactiveUser
    return user


async def get_current_active_admin(
        user: Annotated[BaseUserInfo, Depends(get_current_active_user)],
) -> BaseUserInfo:
    if user.role not in [Roles.ADMIN, Roles.SUPER_ADMIN]:
        raise HTTPExceptionNoPermission
    return user
