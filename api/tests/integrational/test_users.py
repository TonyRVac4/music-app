import uuid

from httpx import AsyncClient

from api.src.domain.auth.utils import verify_password_hash
from api.src.domain.users.schemas import UserDTO
from api.src.infrastructure.app import app


async def get_user(user_id: str) -> UserDTO | None:
    async with app.unit_of_work.execute() as uow:
        return await uow.users.find_by_id(user_id)


class TestCreate:
    async def test_create_user(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/users",
            json={
                "username": "test_user",
                "email": "test_email@gmail.com",
                "password": "1234567890",
            }
        )

        assert response.status_code == 201

        result = response.json()
        assert result.get("password") is None


        user = await get_user(result["id"])
        assert user is not None
        assert user.username == result["username"]
        assert user.email == result["email"]
        assert user.is_active is True
        assert user.is_email_verified is False

    async def test_cant_create_user_with_existing_username(
            self, client: AsyncClient, simple_user: UserDTO,
    ):
        response = await client.post(
            "/api/v1/users",
            json={
                "username": simple_user.username,
                "email": "test_email@gmail.com",
                "password": "1234567890",
            }
        )
        assert response.status_code == 409

    async def test_cant_create_user_with_existing_email(
            self, client: AsyncClient, simple_user: UserDTO,
    ):
        response = await client.post(
            "/api/v1/users",
            json={
                "username": "test_user",
                "email": simple_user.email,
                "password": "1234567890",
            }
        )
        assert response.status_code == 409


class TestGet:
    async def test_unauthenticated_user_cant_get_user(
            self, client: AsyncClient, simple_user: UserDTO,
    ):
        response = await client.get(f"/api/v1/users/{simple_user.id}")
        assert response.status_code == 401

    async def test_user_get_themselves(
            self, user_client: AsyncClient, simple_user: UserDTO,
    ):
        response = await user_client.get(f"/api/v1/users/{simple_user.id}")
        assert response.status_code == 200

        result = response.json()
        assert result["id"] == str(simple_user.id)
        assert result["username"] == simple_user.username
        assert result["email"] == simple_user.email
        assert result["is_active"] == simple_user.is_active
        assert result["is_email_verified"] == simple_user.is_email_verified
        assert result["role"] == simple_user.role

    async def test_user_cant_get_other_user(
            self, user_client: AsyncClient, other_simple_user: UserDTO,
    ):
        response = await user_client.get(f"/api/v1/users/{other_simple_user.id}")
        assert response.status_code == 403

    async def test_admin_get_themselves(
            self, admin_client: AsyncClient, admin_user: UserDTO,
    ):
        response = await admin_client.get(f"/api/v1/users/{admin_user.id}")
        assert response.status_code == 200

        result = response.json()
        assert result["id"] == str(admin_user.id)
        assert result["username"] == admin_user.username
        assert result["email"] == admin_user.email
        assert result["is_active"] == admin_user.is_active
        assert result["is_email_verified"] == admin_user.is_email_verified
        assert result["role"] == admin_user.role

    async def test_admin_get_user(
            self, admin_client: AsyncClient, simple_user: UserDTO,
    ):
        response = await admin_client.get(f"/api/v1/users/{simple_user.id}")
        assert response.status_code == 200

        result = response.json()
        assert result["id"] == str(simple_user.id)
        assert result["username"] == simple_user.username
        assert result["email"] == simple_user.email
        assert result["is_active"] == simple_user.is_active
        assert result["is_email_verified"] == simple_user.is_email_verified
        assert result["role"] == simple_user.role

    async def test_admin_cant_get_superadmin(
            self, admin_client: AsyncClient, superadmin_user: UserDTO,
    ):
        response = await admin_client.get(f"/api/v1/users/{superadmin_user.id}")
        assert response.status_code == 403

    async def test_superadmin_get_themselves(
            self, superadmin_client: AsyncClient, superadmin_user: UserDTO,
    ):
        response = await superadmin_client.get(f"/api/v1/users/{superadmin_user.id}")
        assert response.status_code == 200

        result = response.json()
        assert result["id"] == str(superadmin_user.id)
        assert result["username"] == superadmin_user.username
        assert result["email"] == superadmin_user.email
        assert result["is_active"] == superadmin_user.is_active
        assert result["is_email_verified"] == superadmin_user.is_email_verified
        assert result["role"] == superadmin_user.role

    async def test_superadmin_get_user(
            self, superadmin_client: AsyncClient, simple_user: UserDTO,
    ):
        response = await superadmin_client.get(f"/api/v1/users/{simple_user.id}")
        assert response.status_code == 200

        result = response.json()
        assert result["id"] == str(simple_user.id)
        assert result["username"] == simple_user.username
        assert result["email"] == simple_user.email
        assert result["is_active"] == simple_user.is_active
        assert result["is_email_verified"] == simple_user.is_email_verified
        assert result["role"] == simple_user.role

    async def test_superadmin_get_admin(
            self, superadmin_client: AsyncClient, admin_user: UserDTO,
    ):
        response = await superadmin_client.get(f"/api/v1/users/{admin_user.id}")
        assert response.status_code == 200

        result = response.json()
        assert result["id"] == str(admin_user.id)
        assert result["username"] == admin_user.username
        assert result["email"] == admin_user.email
        assert result["is_active"] == admin_user.is_active
        assert result["is_email_verified"] == admin_user.is_email_verified
        assert result["role"] == admin_user.role

    async def test_get_nonexistent_user(self, admin_client: AsyncClient):
        response = await admin_client.get(f"/api/v1/users/{str(uuid.uuid4())}")
        assert response.status_code == 404


class TestUpdate:
    async def test_unauthenticated_user_cant_update_users(
            self, client: AsyncClient, simple_user: UserDTO,
    ):
        response = await client.put(
            f"/api/v1/users/{simple_user.id}",
            json={
                "username": "new_test_user_name",
            },
        )
        assert response.status_code == 401

    async def test_user_update_themselves(
            self, user_client: AsyncClient, simple_user: UserDTO,
    ):
        response = await user_client.put(
            f"/api/v1/users/{simple_user.id}",
            json={
                "username": "new_test_user_name",
                "email": "new_test_user_email@gmail.com",
                "password": "0987654321",
            },
        )
        assert response.status_code == 204

        user = await get_user(str(simple_user.id))
        assert user.username == "new_test_user_name"
        assert user.email == "new_test_user_email@gmail.com"
        assert verify_password_hash("0987654321", user.password)

    async def test_cant_update_if_username_already_exists(
            self, client: AsyncClient, user_client: AsyncClient, simple_user: UserDTO,
    ):
        response = await client.post(
            "/api/v1/users",
            json={
                "username": "test_user",
                "email": "test_email@gmail.com",
                "password": "1234567890",
            }
        )
        assert response.status_code == 201

        response = await user_client.put(
            f"/api/v1/users/{simple_user.id}",
            json={
                "username": "test_user",
                "email": "new_test_user_email@gmail.com",
            },
        )
        assert response.status_code == 409

    async def test_cant_update_if_email_already_exists(
            self, client: AsyncClient, user_client: AsyncClient, simple_user: UserDTO,
    ):
        response = await client.post(
            "/api/v1/users",
            json={
                "username": "test_user",
                "email": "test_email@gmail.com",
                "password": "1234567890",
            }
        )
        assert response.status_code == 201

        response = await user_client.put(
            f"/api/v1/users/{simple_user.id}",
            json={
                "username": "new_test_user_name",
                "email": "test_email@gmail.com",
            },
        )
        assert response.status_code == 409

    async def test_user_cant_update_other_users(
            self, user_client: AsyncClient, other_simple_user: UserDTO,
    ):
        response = await user_client.put(
            f"/api/v1/users/{other_simple_user.id}",
            json={
                "username": "new_test_user_name",
            },
        )
        assert response.status_code == 403

    async def test_user_cant_update_self_role(
            self, user_client: AsyncClient, simple_user: UserDTO,
    ):
        response = await user_client.put(
            f"/api/v1/users/{simple_user.id}",
            json={
                "role": "ADMIN",
            },
        )
        assert response.status_code == 403

    async def test_user_cant_update_self_is_active(
            self, user_client: AsyncClient, simple_user: UserDTO,
    ):
        response = await user_client.put(
            f"/api/v1/users/{simple_user.id}",
            json={
                "is_active": False,
            },
        )
        assert response.status_code == 403

    async def test_user_cant_update_self_is_email_verified(
            self, user_client: AsyncClient, simple_user: UserDTO,
    ):
        response = await user_client.put(
            f"/api/v1/users/{simple_user.id}",
            json={
                "is_email_verified": False,
            },
        )
        assert response.status_code == 403

    async def test_admin_update_themselves(
            self, admin_client: AsyncClient, admin_user: UserDTO,
    ):
        response = await admin_client.put(
            f"/api/v1/users/{admin_user.id}",
            json={
                "username": "new_test_admin_name",
                "email": "new_test_admin_email@gmail.com",
                "password": "0987654321",
            },
        )
        assert response.status_code == 204

        user = await get_user(str(admin_user.id))
        assert user.username == "new_test_admin_name"
        assert user.email == "new_test_admin_email@gmail.com"
        assert verify_password_hash("0987654321", user.password)

    async def test_admin_cant_update_self_role(
            self, admin_client: AsyncClient, admin_user: UserDTO,
    ):
        response = await admin_client.put(
            f"/api/v1/users/{admin_user.id}",
            json={
                "role": "SUPER_ADMIN",
            },
        )
        assert response.status_code == 403

    async def test_admin_cant_update_self_is_active(
            self, admin_client: AsyncClient, admin_user: UserDTO,
    ):
        response = await admin_client.put(
            f"/api/v1/users/{admin_user.id}",
            json={
                "is_active": False,
            },
        )
        assert response.status_code == 403

    async def test_admin_cant_update_self_is_email_verified(
            self, admin_client: AsyncClient, admin_user: UserDTO,
    ):
        response = await admin_client.put(
            f"/api/v1/users/{admin_user.id}",
            json={
                "is_email_verified": False,
            },
        )
        assert response.status_code == 403

    async def test_admin_update_users(
            self, admin_client: AsyncClient, simple_user: UserDTO,
    ):
        response = await admin_client.put(
            f"/api/v1/users/{simple_user.id}",
            json={
                "username": "new_test_user_name",
                "email": "new_test_user_email@gmail.com",
                "password": "0987654321",
                "is_email_verified": False,
                "is_active": False,
            },
        )
        assert response.status_code == 204

        user = await get_user(str(simple_user.id))
        print(user)
        assert user.username == "new_test_user_name"
        assert user.email == "new_test_user_email@gmail.com"
        assert verify_password_hash("0987654321", user.password)
        assert user.is_active is False
        assert user.is_email_verified is False

    async def test_admin_cant_update_users_role(
            self, admin_client: AsyncClient, simple_user: UserDTO,
    ):
        response = await admin_client.put(
            f"/api/v1/users/{simple_user.id}",
            json={
                "role": "ADMIN",
            },
        )
        assert response.status_code == 403

    async def test_admin_cant_update_other_admins(
            self, admin_client: AsyncClient, other_admin_user: UserDTO,
    ):
        response = await admin_client.put(
            f"/api/v1/users/{other_admin_user.id}",
            json={
                "role": "SUPER_ADMIN",
            },
        )
        assert response.status_code == 403

    async def test_admin_cant_update_superadmins(
            self, admin_client: AsyncClient, superadmin_user: UserDTO,
    ):
        response = await admin_client.put(
            f"/api/v1/users/{superadmin_user.id}",
            json={
                "role": "ADMIN",
            },
        )
        assert response.status_code == 403

    async def test_superadmin_update_users(
            self, superadmin_client: AsyncClient, simple_user: UserDTO,
    ):
        response = await superadmin_client.put(
            f"/api/v1/users/{simple_user.id}",
            json={
                "username": "new_test_user_name",
                "email": "new_test_user_email@gmail.com",
                "password": "0987654321",
                "is_email_verified": False,
                "is_active": False,
                "role": "ADMIN",
            },
        )
        assert response.status_code == 204

        user = await get_user(str(simple_user.id))
        assert user.username == "new_test_user_name"
        assert user.email == "new_test_user_email@gmail.com"
        assert verify_password_hash("0987654321", user.password)
        assert user.is_active is False
        assert user.is_email_verified is False
        assert user.role == "ADMIN"

    async def test_superadmin_update_admins(
            self, superadmin_client: AsyncClient, admin_user: UserDTO,
    ):
        response = await superadmin_client.put(
            f"/api/v1/users/{admin_user.id}",
            json={
                "username": "new_test_admin_name",
                "email": "new_test_admin_email@gmail.com",
                "password": "0987654321",
                "is_email_verified": False,
                "is_active": False,
                "role": "USER",
            },
        )
        assert response.status_code == 204

        user = await get_user(str(admin_user.id))
        assert user.username == "new_test_admin_name"
        assert user.email == "new_test_admin_email@gmail.com"
        assert verify_password_hash("0987654321", user.password)
        assert user.is_active is False
        assert user.is_email_verified is False
        assert user.role == "USER"

    async def test_superadmin_cant_update_themselves(
            self, superadmin_client: AsyncClient, superadmin_user: UserDTO,
    ):
        response = await superadmin_client.put(
            f"/api/v1/users/{superadmin_user.id}",
            json={
                "username": "new_test_superadmin_name",
                "email": "new_test_superadmin_email@gmail.com",
                "password": "0987654321",
                "is_email_verified": False,
                "is_active": False,
                "role": "ADMIN",
            },
        )
        assert response.status_code == 403

    async def test_superadmin_cant_update_other_superadmins(
            self, superadmin_client: AsyncClient, other_superadmin_user: UserDTO,
    ):
        response = await superadmin_client.put(
            f"/api/v1/users/{other_superadmin_user.id}",
            json={
                "username": "new_test_superadmin_name",
                "email": "new_test_superadmin_email@gmail.com",
                "password": "0987654321",
                "is_email_verified": False,
                "is_active": False,
                "role": "ADMIN",
            },
        )
        assert response.status_code == 403

    async def test_update_nonexistent_user(self, admin_client: AsyncClient):
        response = await admin_client.put(
            f"/api/v1/users/{str(uuid.uuid4())}",
            json={
                "username": "new_test_user_name",
            },
        )
        assert response.status_code == 404


class TestDelete:
    async def test_unauthenticated_user_cant_delete_users(
            self, client: AsyncClient, simple_user: UserDTO,
    ):
        response = await client.delete(f"/api/v1/users/{simple_user.id}")
        assert response.status_code == 401

    async def test_user_delete_themselves(
            self, user_client: AsyncClient, simple_user: UserDTO,
    ):
        response = await user_client.delete(f"/api/v1/users/{simple_user.id}")
        assert response.status_code == 204

        user = await get_user(str(simple_user.id))
        assert user is None

    async def test_user_cant_delete_other_users(
            self, user_client: AsyncClient, other_simple_user: UserDTO,
    ):
        response = await user_client.delete(f"/api/v1/users/{other_simple_user.id}")
        assert response.status_code == 403

    async def test_admin_delete_users(
            self, admin_client: AsyncClient, simple_user: UserDTO,
    ):
        response = await admin_client.delete(f"/api/v1/users/{simple_user.id}")
        assert response.status_code == 204

        user = await get_user(str(simple_user.id))
        assert user is None

    async def test_admin_cant_delete_themselves(
            self, admin_client: AsyncClient, admin_user: UserDTO,
    ):
        response = await admin_client.delete(f"/api/v1/users/{admin_user.id}")
        assert response.status_code == 403

    async def test_admin_cant_delete_other_admins(
            self, admin_client: AsyncClient, other_admin_user: UserDTO,
    ):
        response = await admin_client.delete(f"/api/v1/users/{other_admin_user.id}")
        assert response.status_code == 403

    async def test_admin_cant_delete_superadmins(
            self, admin_client: AsyncClient, superadmin_user: UserDTO,
    ):
        response = await admin_client.delete(f"/api/v1/users/{superadmin_user.id}")
        assert response.status_code == 403

    async def test_superadmin_delete_users(
            self, superadmin_client: AsyncClient, simple_user: UserDTO,
    ):
        response = await superadmin_client.delete(f"/api/v1/users/{simple_user.id}")
        assert response.status_code == 204

        user = await get_user(str(simple_user.id))
        assert user is None

    async def test_superadmin_delete_admins(
            self, superadmin_client: AsyncClient, admin_user: UserDTO,
    ):
        response = await superadmin_client.delete(f"/api/v1/users/{admin_user.id}")
        assert response.status_code == 204

        user = await get_user(str(admin_user.id))
        assert user is None

    async def test_superadmin_cant_delete_themselves(
            self, superadmin_client: AsyncClient, superadmin_user: UserDTO,
    ):
        response = await superadmin_client.delete(f"/api/v1/users/{superadmin_user.id}")
        assert response.status_code == 403

    async def test_superadmin_cant_delete_other_superadmins(
            self, superadmin_client: AsyncClient, other_superadmin_user: UserDTO,
    ):
        response = await superadmin_client.delete(f"/api/v1/users/{other_superadmin_user.id}")
        assert response.status_code == 403

    async def test_delete_nonexistent_user(self, admin_client: AsyncClient):
        response = await admin_client.delete(f"/api/v1/users/{str(uuid.uuid4())}")
        assert response.status_code == 404
