from pydantic import BaseModel, Field, EmailStr, UUID4, ConfigDict

from api.src.database.models import Roles


class UserCreate(BaseModel):
    username: str = Field(max_length=32)
    email: EmailStr = Field(max_length=64)
    password: str = Field(min_length=10, max_length=64)


class UserStatus(BaseModel):
    is_active: None | bool


class BaseUserInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    username: str
    email: EmailStr
    is_active: bool
    role: Roles


class TokenInfoOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class TokenData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sub: str
    jti: str
    iat: int
    exp: int
    type: str
