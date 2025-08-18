from pydantic import BaseModel, Field, EmailStr, ConfigDict
from uuid import UUID
from api.src.infrastructure.database.enums import Roles


class UserDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID | None = None
    username: str
    email: str
    password: str = Field(exclude=True)
    is_active: bool = Field(default=True)
    is_email_verified: bool = Field(default=False)
    roles: Roles = Roles.USER


class UserCreateRequest(BaseModel):
    username: str = Field(max_length=32)
    email: EmailStr = Field(max_length=64)
    password: str = Field(min_length=10, max_length=64)


class UserUpdateRequest(BaseModel):
    username: str | None = Field(max_length=32, default=None)
    email: EmailStr | None = Field(max_length=64, default=None)
    password: str | None = Field(min_length=10, max_length=64, default=None)
    is_active: None | bool = None
    is_email_verified: None | bool = None
    role: None | Roles = None


# возможно нет необходимости из за UserDTO
class BaseUserInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    email: EmailStr
    is_active: bool
    is_email_verified: bool
    role: Roles


class TokenInfoResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class TokenDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sub: str
    jti: str
    iat: int
    exp: int
    type: str
