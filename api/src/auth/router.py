from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from .schemas import UserCreate, UserInfoOut, TokenInfoOut
from .dependencies import get_auth_service_dependency, get_user_service_dependency
from .service import UserService, AuthService


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register/",
    status_code=status.HTTP_201_CREATED,
    response_model=UserInfoOut,
)
async def register(
        new_user: UserCreate,
        user_service: Annotated[UserService, Depends(get_user_service_dependency)],
) -> UserInfoOut:
    return await user_service.register_new_user(new_user)


@router.post("/login/", response_model=TokenInfoOut)
async def login(
        credentials: Annotated[OAuth2PasswordRequestForm, Depends()],
        auth_service: Annotated[AuthService, Depends(get_auth_service_dependency)],
) -> TokenInfoOut:
    user = await auth_service.authenticate_user(
        credentials.username, credentials.password
    )
    access_token = await auth_service.create_access_token(user)
    refresh_token = await auth_service.create_refresh_token(user)

    return {"access_token": access_token, "refresh_token": refresh_token}
