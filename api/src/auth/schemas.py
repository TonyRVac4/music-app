from pydantic import BaseModel, Field, EmailStr, UUID4

from api.src.database.models import Roles


class UserCreate(BaseModel):
    username: str = Field(max_length=32)
    email: EmailStr = Field(max_length=64)
    password: str = Field(min_length=10, max_length=64)


class UserInfoOut(BaseModel):
    id: UUID4
    username: str
    email: EmailStr
    role: Roles


class TokenInfoOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
