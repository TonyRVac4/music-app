from httpx import AsyncClient
from datetime import datetime, timedelta, timezone

from api.src.domain.users.schemas import UserDTO
from api.src.domain.auth.utils import decode_jwt
from api.src.domain.auth.schemas import TokenDTO
from api.src.infrastructure.app import app
from api.src.infrastructure.settings import settings


async def get_refresh_token(jti: str) -> TokenDTO | None:
    async with app.unit_of_work.execute() as uow:
        return await uow.refresh_tokens.find_by(token_id=jti)


class TestLogin:
    async def test_login_by_username(
            self, client: AsyncClient, simple_user: UserDTO,
    ):
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": simple_user.username,
                "password": "verysecurepassword123",
            }
        )
        assert response.status_code == 200

        result = response.json()
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "Bearer"

        # проверка того что токен сохранился в базе
        refresh_token_id = decode_jwt(result["refresh_token"])["jti"]
        assert await get_refresh_token(refresh_token_id) is not None

    async def test_login_by_email(
            self, client: AsyncClient, simple_user: UserDTO,
    ):
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": simple_user.email,
                "password": "verysecurepassword123",
            }
        )
        assert response.status_code == 200

        result = response.json()
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "Bearer"

        # проверка того что токен сохранился в базе
        decoded_token = decode_jwt(result["refresh_token"])
        assert await get_refresh_token(decoded_token["jti"]) is not None

    async def test_cant_login_with_invalid_email(
            self, client: AsyncClient, simple_user: UserDTO,
    ):
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "password": simple_user.password,
                "username": "invalid_email",
            }
        )
        assert response.status_code == 401

    async def test_cant_login_with_invalid_username(
            self, client: AsyncClient, simple_user: UserDTO,
    ):
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "password": simple_user.password,
                "username": "invalid_username",
            }
        )
        assert response.status_code == 401

    async def test_cant_login_with_invalid_password(
            self, client: AsyncClient, simple_user: UserDTO,
    ):
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "password": "invalid_pasword",
                "username": simple_user.username,
            }
        )
        assert response.status_code == 401

    async def test_inactive_user_cant_login(
            self, client: AsyncClient, inactive_user: UserDTO,
    ):
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": inactive_user.username,
                "password": "verysecurepassword123",
            }
        )
        assert response.status_code == 403

    async def test_tokens_exp_data_is_correct(
            self, user_client: AsyncClient, simple_user: UserDTO,
    ):
        access_token_exp_date = decode_jwt(user_client.cookies.get("access_token"))["exp"]
        refresh_token_exp_date = decode_jwt(user_client.cookies.get("refresh_token"))["exp"]

        time_now = datetime.now(tz=timezone.utc).timestamp()
        access_exp_time = time_now + timedelta(minutes=settings.auth.access_token_expires_min).total_seconds()
        refresh_exp_time = time_now + timedelta(minutes=settings.auth.refresh_token_expires_min).total_seconds()

        assert abs(access_token_exp_date - access_exp_time) < 1.0
        assert abs(refresh_token_exp_date - refresh_exp_time) < 1.0


class TestLogout:
    async def test_logout(
            self, user_client: AsyncClient, simple_user: UserDTO,
    ):
        refresh_token = user_client.cookies.get("refresh_token")
        refresh_token_id = decode_jwt(refresh_token)["jti"]

        token_before_logout = await get_refresh_token(refresh_token_id)
        assert token_before_logout is not None

        response = await user_client.post(
            "api/v1/auth/logout",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )
        assert response.status_code == 204

        token_after = await get_refresh_token(refresh_token_id)
        assert token_after is None

    async def test_cant_logout_with_access_token(
            self, user_client: AsyncClient, simple_user: UserDTO,
    ):
        refresh_token_id = decode_jwt(user_client.cookies.get("refresh_token"))["jti"]

        token_before_logout = await get_refresh_token(refresh_token_id)
        assert token_before_logout is not None

        response = await user_client.post(
            "api/v1/auth/logout",
            headers={"Authorization": f"Bearer {user_client.cookies.get("access_token")}"},
        )
        assert response.status_code == 401

        token_before_logout = await get_refresh_token(refresh_token_id)
        assert token_before_logout is not None
