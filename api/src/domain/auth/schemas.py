from pydantic import BaseModel, ConfigDict


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
