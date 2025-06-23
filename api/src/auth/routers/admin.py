import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status

from api.src.auth.exceptions import HTTPExceptionNoPermission
from api.src.auth.schemas import BaseUserInfo, UserAdminUpdate
from api.src.auth.dependencies import get_user_service_dependency, get_current_active_admin
from api.src.auth.service import UserService
from api.src.auth.utils import check_permissions
from api.src.database.models import Roles

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.patch(
    "/user/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def admin_update_user_is_active(
        user_id: str,
        data: UserAdminUpdate,
        admin: Annotated[BaseUserInfo, Depends(get_current_active_admin)],
        user_service: Annotated[UserService, Depends(get_user_service_dependency)],
):
    target_user: BaseUserInfo = await user_service.get_user_by_id(user_id)
    check_permissions(admin, target_user)

    if data.role and admin.role != Roles.SUPER_ADMIN:
        raise HTTPExceptionNoPermission

    await user_service.update(user_id, **data.model_dump(exclude_none=True))
