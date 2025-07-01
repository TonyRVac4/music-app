import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status

from api.src.users.exceptions import HTTPExceptionNoPermission
from api.src.users.schemas import BaseUserInfo, UserAdminUpdate
from api.src.users.dependencies import get_user_service_dependency
from api.src.dependencies.auth_deps import get_current_active_admin
from api.src.users.services import UserService
from api.src.users.utils import check_permissions
from api.src.database.enums import Roles

logger = logging.getLogger("my_app")

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.patch(
    "/user/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def admin_update_user_is_active_and_role(
        user_id: str,
        data: UserAdminUpdate,
        admin: Annotated[BaseUserInfo, Depends(get_current_active_admin)],
        user_service: Annotated[UserService, Depends(get_user_service_dependency)],
):
    target_user: BaseUserInfo = await user_service.get_user_by_id(user_id)
    check_permissions(admin, target_user)

    if data.role and admin.role != Roles.SUPER_ADMIN:
        logger.warning(
            "Admin:\n"
            f"'{admin.role}:{admin.username}:{admin.id}:' "
            f"tried to update user role for "
            f"'{target_user.role}:{target_user.username}:{target_user.id}'!"
            f"Values: {data.model_dump(exclude_none=True)}"
        )
        raise HTTPExceptionNoPermission

    await user_service.update(user_id, **data.model_dump(exclude_none=True))

    logger.warning(
        f"Admin:\n"
        f"'{admin.role}:{admin.username}:{admin.id}:' "
        f"updated "
        f"'{target_user.role}:{target_user.username}:{target_user.id}'\n"
        f"Values: {data.model_dump(exclude_none=True)}"
    )
