from typing import Annotated

from fastapi import APIRouter, Depends, status, BackgroundTasks
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
        background_tasks: BackgroundTasks,
        user_service: Annotated[UserService, Depends(get_user_service_dependency)],
) -> UserInfoOut:
    result = await user_service.register_new_user(user=new_user)
    await user_service.send_verification_code(result.email, background_tasks)
    return result


@router.get(
    "/resend_email_verification_code/",
    status_code=status.HTTP_202_ACCEPTED,
)
async def resend_email_verification_code(
        email: str,
        background_tasks: BackgroundTasks,
        user_service: Annotated[UserService, Depends(get_user_service_dependency)],
) -> dict:
    await user_service.check_user_exist_by_email_and_is_not_verified(email=email)
    await user_service.send_verification_code(email, background_tasks)
    return {"message": "Verification email has been resent."}


@router.get("/verify_email/")
async def verify_email(
        email: str, code: str,
        user_service: Annotated[UserService, Depends(get_user_service_dependency)],
) -> dict:
    await user_service.check_user_exist_by_email_and_is_not_verified(email=email)
    await user_service.confirm_verification_code(email=email, code=code)
    return {"message": "Email successfully verified."}


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
