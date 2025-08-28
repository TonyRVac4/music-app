import pytest
from httpx import ASGITransport, AsyncClient

from api.src.main import app
from api.src.infrastructure.app import app as app_container
from api.src.infrastructure.database.enums import Roles
from api.src.infrastructure.database.models import Base
from api.src.domain.users.schemas import UserDTO
from api.src.domain.auth.utils import get_password_hash


@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    async with app_container._sqlalchemy_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with app_container._sqlalchemy_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def simple_user() -> UserDTO:
    async with app_container.unit_of_work.begin() as uow:
        return await uow.users.create(
            UserDTO(
                username="usertestsubject1",
                email="emailusertestsubject1@gmail.com",
                password=get_password_hash("verysecurepassword123"),
                is_active=True,
                is_email_verified=True,
                role=Roles.USER,
            )
        )


@pytest.fixture
async def other_simple_user() -> UserDTO:
    async with app_container.unit_of_work.begin() as uow:
        return await uow.users.create(
            UserDTO(
                username="usertestsubject2",
                email="emailusertestsubject2@gmail.com",
                password=get_password_hash("verysecurepassword123"),
                is_active=True,
                is_email_verified=True,
                role=Roles.USER,
            )
        )


@pytest.fixture
async def inactive_user() -> UserDTO:
    async with app_container.unit_of_work.begin() as uow:
        return await uow.users.create(
            UserDTO(
                username="usertestsubject1",
                email="emailusertestsubject1@gmail.com",
                password=get_password_hash("verysecurepassword123"),
                is_active=False,
                is_email_verified=True,
                role=Roles.USER,
            )
        )


@pytest.fixture
async def admin_user() -> UserDTO:
    async with app_container.unit_of_work.begin() as uow:
        return await uow.users.create(
            UserDTO(
                username="admintestsubject1",
                email="emailadmintestsubject1@gmail.com",
                password=get_password_hash("verysecurepassword123"),
                is_active=True,
                is_email_verified=True,
                role=Roles.ADMIN,
            )
        )


@pytest.fixture
async def other_admin_user() -> UserDTO:
    async with app_container.unit_of_work.begin() as uow:
        return await uow.users.create(
            UserDTO(
                username="admintestsubject2",
                email="emailadmintestsubject2@gmail.com",
                password=get_password_hash("verysecurepassword123"),
                is_active=True,
                is_email_verified=True,
                role=Roles.ADMIN,
            )
        )


@pytest.fixture
async def superadmin_user() -> UserDTO:
    async with app_container.unit_of_work.begin() as uow:
        return await uow.users.create(
            UserDTO(
                username="superadmintestsubject1",
                email="emailsuperadmintestsubject1@gmail.com",
                password=get_password_hash("verysecurepassword123"),
                is_active=True,
                is_email_verified=True,
                role=Roles.SUPER_ADMIN,
            )
        )


@pytest.fixture
async def other_superadmin_user() -> UserDTO:
    async with app_container.unit_of_work.begin() as uow:
        return await uow.users.create(
            UserDTO(
                username="superadmintestsubject2",
                email="emailsuperadmintestsubject2@gmail.com",
                password=get_password_hash("verysecurepassword123"),
                is_active=True,
                is_email_verified=True,
                role=Roles.SUPER_ADMIN,
            )
        )


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test",
    ) as client:
        yield client


@pytest.fixture
async def user_client(simple_user):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test",
    ) as client:
        new_login = await client.post(
            "/api/v1/auth/login",
            data={"username": simple_user.username, "password": "verysecurepassword123"},
        )
        result = new_login.json()
        client.headers["Authorization"] = f"{result["token_type"]} {result["access_token"]}"
        client.cookies.set("refresh_token", result["refresh_token"])
        client.cookies.set("access_token", result["access_token"])
        yield client


@pytest.fixture
async def admin_client(admin_user):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test",
    ) as client:
        new_login = await client.post(
            "/api/v1/auth/login",
            data={"username": admin_user.username, "password": "verysecurepassword123"},
        )
        result = new_login.json()
        client.headers["Authorization"] = f"{result["token_type"]} {result["access_token"]}"
        client.cookies.set("refresh_token", result["refresh_token"])
        client.cookies.set("access_token", result["access_token"])
        yield client


@pytest.fixture
async def superadmin_client(superadmin_user):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test",
    ) as client:
        new_login = await client.post(
            "/api/v1/auth/login",
            data={"username": superadmin_user.username, "password": "verysecurepassword123"},
        )
        result = new_login.json()
        client.headers["Authorization"] = f"{result["token_type"]} {result["access_token"]}"
        client.cookies.set("refresh_token", result["refresh_token"])
        client.cookies.set("access_token", result["access_token"])
        yield client
