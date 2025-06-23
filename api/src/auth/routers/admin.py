import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status

from api.src.auth.exceptions import HTTPExceptionNotModified
from api.src.auth.schemas import BaseUserInfo
from api.src.auth.dependencies import get_user_service_dependency, get_current_active_admin
from api.src.auth.service import UserService
from api.src.auth.utils import check_permissions


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.patch(
    "/user/deactivate/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def deactivate_user_by_id(
        user_id: str,
        admin: Annotated[BaseUserInfo, Depends(get_current_active_admin)],
        user_service: Annotated[UserService, Depends(get_user_service_dependency)],
):
    target_user: BaseUserInfo = await user_service.get_user_by_id(user_id)
    check_permissions(admin, target_user)

    if not target_user.is_active:
        raise HTTPExceptionNotModified

    await user_service.update_is_active(user_id, is_active=False)


@router.patch(
    "/user/activate/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def deactivate_user_by_id(
        user_id: str,
        admin: Annotated[BaseUserInfo, Depends(get_current_active_admin)],
        user_service: Annotated[UserService, Depends(get_user_service_dependency)],
):
    target_user: BaseUserInfo = await user_service.get_user_by_id(user_id)
    check_permissions(admin, target_user)

    if target_user.is_active:
        raise HTTPExceptionNotModified

    await user_service.update_is_active(user_id, is_active=True)
