import logging

from .schemas import UserCreateRequest, UserDTO, UserUpdateRequest
from .exceptions import (
    HTTPExceptionUserAlreadyExists,
    HTTPExceptionEmailNotFound,
    HTTPExceptionUserNotFound,
    HTTPExceptionEmailAlreadyVerified,
)
from api.src.domain.auth.utils import get_password_hash
from api.src.infrastructure.dal.uow import AbstractUnitOfWork
from api.src.infrastructure.dal.datasource import AbstractUnitDataSource

from api.src.infrastructure.database.exceptions import (
    ConstraintViolation,
    EntityNotFound,
)


logger = logging.getLogger("my_app")


class UserService:
    def __init__(
        self,
        unit_of_work: AbstractUnitOfWork[AbstractUnitDataSource],
    ):
        self.uow = unit_of_work

    async def create(self, user: UserCreateRequest) -> UserDTO:
        async with self.uow.begin() as datasource:
            new_user = UserDTO(
                username=user.username,
                email=str(user.email),
                password=get_password_hash(user.password),
            )

            try:
                result: UserDTO = await datasource.users.create(data=new_user)
            except ConstraintViolation:
                logger.info(
                    f"Registration: User with given credentials already exists! ({user.username}, {user.email})"
                )
                raise HTTPExceptionUserAlreadyExists

            logger.info(
                f"Registration: Account created!\nUsername:{user.username} | Email:{user.email}"
            )
            return result

    async def get_by_id(self, user_id: str) -> UserDTO:
        async with self.uow.execute() as datasource:
            user = await datasource.users.find_by_id(_id=user_id)
            if not user:
                logger.info(f"User with id: '{user_id}' does not exist!")
                raise HTTPExceptionUserNotFound
            return user

    async def check_user_exist_by_email_and_is_not_verified(self, email: str) -> None:
        async with self.uow.execute() as datasource:
            user = await datasource.users.find_by(email=email)

        if not user:
            logger.info(f"User with email: '{email}' does not exist!")
            raise HTTPExceptionEmailNotFound
        if user.is_email_verified:
            logger.info(f"User with email: '{email}' is already verified!")
            raise HTTPExceptionEmailAlreadyVerified

    async def is_user_active(self, user_id: str) -> bool:
        user = await self.get_by_id(user_id)
        if not user.is_active:
            return False
        return True

    async def update(self, user_id: str, data: UserUpdateRequest) -> None:
        async with self.uow.begin() as datasource:
            user = await self.get_by_id(user_id)
            if data.email != user.email:
                data.is_email_verified = False
            if data.password:
                data.password = get_password_hash(data.password)

            try:
                await datasource.users.update(user_id, UserDTO.model_validate(data))
            except EntityNotFound:
                raise HTTPExceptionUserNotFound
            except ConstraintViolation:
                raise HTTPExceptionUserAlreadyExists

    async def delete(self, user_id: str) -> None:
        async with self.uow.begin() as datasource:
            await datasource.users.delete(user_id)
