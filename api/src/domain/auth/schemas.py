import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class RefreshTokenDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    token_id: str
    expires_at: datetime.datetime
    user_id: UUID


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
