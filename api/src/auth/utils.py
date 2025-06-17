import smtplib
import email
from uuid import uuid4
from datetime import datetime, timedelta

from jose import jwt
import redis.asyncio as redis
from passlib.context import CryptContext

from api.src.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async_redis_client = redis.from_url(settings.redis_db_url)


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


def send_email(to_email: str, message: str) -> None:
    with smtplib.SMTP('smtp.gmail.com', 587) as smtpObj:
        smtpObj.starttls()
        smtpObj.login(user=settings.APP_EMAIL, password=settings.APP_EMAIL_PASSWORD)
        m = email.message.Message()
        m['From'] = settings.APP_EMAIL
        m['To'] = to_email
        m['Subject'] = "Music App email verification."

        m.set_payload(message)
        smtpObj.sendmail(from_addr=settings.APP_EMAIL, to_addrs=to_email, msg=m.as_string())
