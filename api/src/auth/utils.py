from uuid import uuid4
from datetime import datetime, timedelta

from passlib.context import CryptContext
from jose import jwt

from api.src.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password_hash(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_jwt(payload: dict, token_type: str, expires_minutes: int) -> str:
    time_now = datetime.utcnow()
    expiration_time = time_now + timedelta(minutes=expires_minutes)

    payload.update(
        {
            "exp": expiration_time,
            "iat": time_now,
            "jti": str(uuid4()),
            settings.TOKEN_TYPE_FILED_NAME: token_type
        }
    )

    return jwt.encode(payload, key=settings.JWT_KEY, algorithm=settings.JWT_ALGORITHM)
