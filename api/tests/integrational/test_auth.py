import asyncio
from datetime import datetime, timedelta, timezone

from httpx import AsyncClient

from api.src.domain.users.schemas import UserDTO
from api.src.domain.auth.utils import decode_jwt
from api.src.domain.auth.schemas import TokenDTO
from api.src.infrastructure.app import app
from api.src.infrastructure.settings import settings


async def get_refresh_token(jti: str) -> TokenDTO | None:
    async with app.unit_of_work.execute() as uow:
        return await uow.refresh_tokens.find_by_id(jti)


async def get_list_of_tokens(user_id: str) -> list[TokenDTO]:
    async with app.unit_of_work.execute() as uow:
        return await uow.refresh_tokens.list_all(user_id=user_id)


async def make_user_inactive(user_id: str) -> None:
    async with app.unit_of_work.begin() as uow:
        user = await uow.users.find_by_id(user_id)
        user.is_active = False
        await uow.users.update(user_id, user)


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
            self, user_client: AsyncClient,
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
            self, user_client: AsyncClient,
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


class TestRefreshToken:
    async def test_refresh_token(
            self, user_client: AsyncClient,
    ):
        old_access_token = user_client.cookies.get("access_token")
        old_refresh_token = user_client.cookies.get("refresh_token")

        # нужен для того чтобы refresh отличались
        await asyncio.sleep(1)

        response = await user_client.post(
            "/api/v1/auth/refresh-token",
            headers={"Authorization": f"Bearer {old_refresh_token}"},
        )
        assert response.status_code == 200

        result = response.json()
        new_access_token = result.get("access_token")
        new_refresh_token = result.get("refresh_token")

        assert new_access_token is not None
        assert new_refresh_token is not None
        assert result["token_type"] == "Bearer"

        assert result["access_token"] != old_access_token
        assert result["refresh_token"] != old_refresh_token

        decoded_old_access_token = decode_jwt(old_access_token)
        decoded_old_refresh_token = decode_jwt(old_refresh_token)
        decoded_new_access_token = decode_jwt(new_access_token)
        decoded_new_refresh_token = decode_jwt(new_refresh_token)

        # старый и новый refresh не должны отличаются дрг от друга больше чем на 2 минуты
        assert abs(decoded_new_refresh_token["exp"] - decoded_old_refresh_token["exp"]) < 120
        assert decoded_new_access_token["exp"] != decoded_old_access_token["exp"]

        # проверка замены refresh в базе
        old_refresh_in_db = await get_refresh_token(decoded_old_refresh_token["jti"])
        new_refresh_in_db = await get_refresh_token(decoded_new_refresh_token["jti"])
        assert old_refresh_in_db is None
        assert new_refresh_in_db is not None

    async def test_cant_refresh_with_access_token(
            self, user_client: AsyncClient,
    ):
        old_access_token = user_client.cookies.get("access_token")

        response = await user_client.post(
            "/api/v1/auth/refresh-token",
            headers={"Authorization": f"Bearer {old_access_token}"},
        )
        assert response.status_code == 401

    async def test_cant_refresh_with_expired_refresh_token(
            self, user_client: AsyncClient, simple_user: UserDTO,
    ):
        expired_refresh_token = await app.auth_service.create_refresh_token(simple_user.id, expires_in_min=0)
        decoded_expired_refresh_token = decode_jwt(expired_refresh_token)
        await app.auth_service.save_refresh_token(
            user_id=str(simple_user.id),
            jti=decoded_expired_refresh_token["jti"],
            exp_date_stamp=decoded_expired_refresh_token["exp"]
        )
        await asyncio.sleep(2)

        response = await user_client.post(
            "/api/v1/auth/refresh-token",
            headers={"Authorization": f"Bearer {expired_refresh_token}"},
        )
        assert response.status_code == 401

    async def test_inactive_user_cant_refresh_token(
            self, user_client: AsyncClient, simple_user: UserDTO,
    ):
        await make_user_inactive(str(simple_user.id))

        old_refresh_token = user_client.cookies.get("refresh_token")

        response = await user_client.post(
            "/api/v1/auth/refresh-token",
            headers={"Authorization": f"Bearer {old_refresh_token}"},
        )
        assert response.status_code == 403

    async def test_cant_refresh_if_refresh_token_not_in_db(
            self, user_client: AsyncClient,
    ):
        old_refresh_token = user_client.cookies.get("refresh_token")
        old_refresh_token_id = decode_jwt(old_refresh_token)["jti"]

        token_before = await get_refresh_token(old_refresh_token_id)
        async with app.unit_of_work.begin() as uow:
            await uow.refresh_tokens.delete(old_refresh_token_id)
        token_after = await get_refresh_token(old_refresh_token_id)

        assert token_before is not None
        assert token_after is None

        response = await user_client.post(
            "/api/v1/auth/refresh-token",
            headers={"Authorization": f"Bearer {old_refresh_token}"},
        )
        assert response.status_code == 401


class TestTerminateAllSessions:
    async def test_unauthenticated_user_cant_terminate_sessions(
            self, client: AsyncClient, simple_user: UserDTO,
    ):
        response = await client.post(
            f"/api/v1/auth/terminate-all-sessions/{simple_user.id}",
        )
        assert response.status_code == 401

    async def test_user_terminate_all_self_sessions(
            self, user_client: AsyncClient, simple_user: UserDTO,
    ):
        tokens_before = await get_list_of_tokens(str(simple_user.id))
        assert len(tokens_before) > 0

        response = await user_client.post(
            f"/api/v1/auth/terminate-all-sessions/{simple_user.id}",
        )
        assert response.status_code == 204

        tokens_after = await get_list_of_tokens(str(simple_user.id))
        assert len(tokens_after) == 0

    async def test_admin_terminate_all_user_sessions(
            self,
            admin_client: AsyncClient,
            user_client: AsyncClient,
            simple_user: UserDTO,
    ):
        tokens_before = await get_list_of_tokens(str(simple_user.id))
        assert len(tokens_before) > 0

        response = await admin_client.post(
            f"/api/v1/auth/terminate-all-sessions/{simple_user.id}",
        )
        assert response.status_code == 204

        tokens_after = await get_list_of_tokens(str(simple_user.id))
        assert len(tokens_after) == 0

    async def test_admin_terminate_all_self_sessions(
            self, admin_client: AsyncClient, admin_user: UserDTO,
    ):
        tokens_before = await get_list_of_tokens(str(admin_user.id))
        assert len(tokens_before) > 0

        response = await admin_client.post(
            f"/api/v1/auth/terminate-all-sessions/{admin_user.id}",
        )
        assert response.status_code == 204

        tokens_after = await get_list_of_tokens(str(admin_user.id))
        assert len(tokens_after) == 0

    async def test_admin_cant_terminate_all_superadmin_sessions(
            self, admin_client: AsyncClient, superadmin_user: UserDTO,
    ):
        response = await admin_client.post(
            f"/api/v1/auth/terminate-all-sessions/{superadmin_user.id}",
        )
        assert response.status_code == 403

    async def test_superadmin_terminate_all_user_sessions(
            self,
            superadmin_client: AsyncClient,
            user_client: AsyncClient,
            simple_user: UserDTO,
    ):
        tokens_before = await get_list_of_tokens(str(simple_user.id))
        assert len(tokens_before) > 0

        response = await superadmin_client.post(
            f"/api/v1/auth/terminate-all-sessions/{simple_user.id}",
        )
        assert response.status_code == 204

        tokens_after = await get_list_of_tokens(str(simple_user.id))
        assert len(tokens_after) == 0

    async def test_superadmin_terminate_all_admin_sessions(
            self,
            superadmin_client: AsyncClient,
            admin_client: AsyncClient,
            admin_user: UserDTO,
    ):
        tokens_before = await get_list_of_tokens(str(admin_user.id))
        assert len(tokens_before) > 0

        response = await superadmin_client.post(
            f"/api/v1/auth/terminate-all-sessions/{admin_user.id}",
        )
        assert response.status_code == 204

        tokens_after = await get_list_of_tokens(str(admin_user.id))
        assert len(tokens_after) == 0


# class TestEmailVerification:
#     ...