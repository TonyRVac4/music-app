import pytest
import faker
from httpx import ASGITransport, AsyncClient

from api.src.main import app
from api.src.infrastructure.app import app as app_container
from api.src.infrastructure.database.enums import Roles
from api.src.infrastructure.database.models import Base
from api.src.domain.users.schemas import UserDTO
from api.src.domain.auth.utils import get_password_hash


fake = faker.Faker()


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    async with app_container._sqlalchemy_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with app_container._sqlalchemy_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def simple_user() -> UserDTO:
    async with app_container.unit_of_work.begin() as uow:
        return await uow.users.create(
            UserDTO(
                username=fake.user_name(),
                email=fake.email(),
                password=get_password_hash("verysecurepassword123"),
                is_active=True,
                is_email_verified=True,
                role=Roles.USER,
            )
        )


@pytest.fixture
async def admin_user() -> UserDTO:
    async with app_container.unit_of_work.begin() as uow:
        return await uow.users.create(
            UserDTO(
                username=fake.user_name(),
                email=fake.email(),
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
                username=fake.user_name(),
                email=fake.email(),
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
        client.headers["Authorization"] = new_login.json()["access_token"]
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
        client.headers["Authorization"] = new_login.json()["access_token"]
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
        client.headers["Authorization"] = new_login.json()["access_token"]
        yield client
