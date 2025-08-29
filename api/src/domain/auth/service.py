import logging
import datetime
from uuid import uuid4, UUID

from sqlalchemy import or_

from api.src.domain.auth.exceptions import (
    HTTPExceptionInvalidToken,
    HTTPExceptionInvalidLoginCredentials,
    HTTPExceptionInvalidEmailVerification,
    HTTPExceptionInactiveUser,
)
from api.src.domain.users.models import SQLAlchemyUserModel
from api.src.domain.users.schemas import UserDataResponse
from api.src.domain.auth.utils import verify_password_hash, create_jwt, send_email
from api.src.infrastructure.dal.datasource import AbstractUnitDataSource
from api.src.infrastructure.dal.uow import AbstractUnitOfWork
from api.src.infrastructure.settings import settings
from api.src.infrastructure.database.exceptions import EntityNotFound
from .schemas import RefreshTokenDTO
from .models import SQLAlchemyRefreshTokenModel


logger = logging.getLogger("my_app")


class AuthService:
    def __init__(
        self,
        unit_of_work: AbstractUnitOfWork[AbstractUnitDataSource],
        redis_client,
    ):
        self.uow = unit_of_work
        self._redis_client = redis_client

    async def authenticate_user(self, login, password) -> UserDataResponse:
        async with self.uow.execute() as datasource:
            user = await datasource.users.find_by(
                or_(
                    SQLAlchemyUserModel.username == login,
                    SQLAlchemyUserModel.email == login,
                )
            )
        if not user:
            logger.warning(f"Authentication: Invalid login! '{login}' does not exist!")
            raise HTTPExceptionInvalidLoginCredentials
        if not verify_password_hash(password, user.password):
            logger.warning(f"Authentication: Invalid password! | '{login}'")
            raise HTTPExceptionInvalidLoginCredentials
        if not user.is_active:
            logger.warning(f"Authentication: Inactive account! | '{login}'")
            raise HTTPExceptionInactiveUser
        # if not user.is_email_verified:
        #     logger.warning(f"Authentication: Email is not verified! | '{login}'")
        #     raise HTTPExceptionInactiveUser

        return UserDataResponse.model_validate(user)

    @staticmethod
    async def create_access_token(
        sub: str,
        expires_in_min: int = settings.auth.access_token_expires_min,
        token_type: str = settings.auth.access_token_name,
    ) -> str:
        payload = {
            "sub": str(sub),
        }
        return create_jwt(payload, token_type, expires_in_min)

    @staticmethod
    async def create_refresh_token(
        sub: str,
        expires_in_min: int = settings.auth.refresh_token_expires_min,
        token_type: str = settings.auth.refresh_token_name,
    ) -> str:
        payload = {
            "sub": str(sub),
        }
        return create_jwt(payload, token_type, expires_in_min)

    async def send_verification_code(self, email: str, background_task) -> None:
        code = str(uuid4())
        async with self._redis_client() as client:
            await client.set(email, code, ex=600)

        url = settings.app.get_verification_link(email, code)
        background_task.add_task(send_email, email, url)
        logger.info(f"Email verification: Code sent! Email: '{email}'")

    async def confirm_verification_code(self, email: str, code: str) -> None:
        async with self._redis_client() as client:
            redis_code = await client.get(email)

        if not redis_code or code != redis_code:
            logger.warning(
                f"Email verification: Invalid verification code! | '{email}'"
            )
            raise HTTPExceptionInvalidEmailVerification

        async with self.uow.begin() as datasource:
            user = await datasource.users.find_by(email=email)
            user.is_email_verified = True
            await datasource.users.update(user.id, user)

        async with self._redis_client() as client:
            await client.delete(email)

        logger.info(
            f"Email verification: Code confirmed, account activated. | '{email}'"
        )

    async def check_refresh_token_exist(self, jti: str) -> None:
        async with self.uow.execute() as datasource:
            token = await datasource.refresh_tokens.find_by_id(jti)
            if not token:
                logger.warning(
                    f"Authorization: "
                    f"Refresh token is valid but not in user active tokens!\n"
                    f"JTI: '{jti}'"
                )
                raise HTTPExceptionInvalidToken

    async def save_refresh_token(
        self, user_id: str, jti: str, exp_date_stamp: int, limit: int = 5,
    ):
        # await self.delete_expired_refresh_tokens()

        async with self.uow.begin() as datasource:
            new_token = RefreshTokenDTO(
                jti=UUID(jti),
                user_id=UUID(user_id),
                expires_at=datetime.datetime.fromtimestamp(exp_date_stamp),
            )
            await datasource.refresh_tokens.create(new_token)

            user_tokens = await datasource.refresh_tokens.list_all(user_id=user_id)
            if len(user_tokens) > limit:
                await datasource.refresh_tokens.delete(user_tokens[0].id)

    async def delete_refresh_token(self, jti: str) -> None:
        async with self.uow.begin() as datasource:
            await datasource.refresh_tokens.delete(jti)

    async def delete_expired_refresh_tokens(self) -> None:
        async with self.uow.begin() as datasource:

            await datasource.refresh_tokens.delete_by(
                SQLAlchemyRefreshTokenModel.expires_at <= datetime.datetime.now(datetime.UTC)
            )

    async def delete_all_refresh_tokens_by_user_id(self, user_id: str) -> None:
        async with self.uow.begin() as datasource:
            await datasource.refresh_tokens.delete_by(user_id=user_id)
