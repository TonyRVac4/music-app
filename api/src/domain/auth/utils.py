import email
import logging
import smtplib
from datetime import datetime, timedelta
from uuid import uuid4

from jose import jwt
from passlib.context import CryptContext

from api.src.domain.users.schemas import UserDTO
from api.src.infrastructure.database.enums import Roles
from api.src.infrastructure.settings import settings


logger = logging.getLogger("my_app")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password_hash(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def decode_jwt(token: str) -> dict:
    return jwt.decode(token, key=settings.auth.jwt_key, algorithms=[settings.auth.jwt_algorithm])


def create_jwt(payload: dict, token_type: str, expires_minutes: int) -> str:
    time_now = datetime.now()
    expiration_time = time_now + timedelta(minutes=expires_minutes)

    payload.update(
        {
            "exp": round(expiration_time.timestamp()),
            "iat": round(time_now.timestamp()),
            "jti": str(uuid4()),
            settings.auth.token_type_filed_name: token_type
        }
    )

    return jwt.encode(payload, key=settings.auth.jwt_key, algorithm=settings.auth.jwt_algorithm)


def send_email(to_email: str, message: str) -> None:
    with smtplib.SMTP('smtp.gmail.com', 587) as smtpObj:
        smtpObj.starttls()
        smtpObj.login(user=settings.email_client.email, password=settings.email_client.password)
        m = email.message.Message()
        m['From'] = settings.email_client.email
        m['To'] = to_email
        m['Subject'] = "Music App email verification."

        m.set_payload(message)
        smtpObj.sendmail(from_addr=settings.email_client.email, to_addrs=to_email, msg=m.as_string())


def validate_token_type(token_type: str, target_type: str) -> bool:
    if target_type == token_type:
        return True
    return False


def check_permissions(current_user: UserDTO, target_user: UserDTO) -> bool:
    allowed: bool = True

    if current_user.id != target_user.id:
        if current_user.role == Roles.USER:
            allowed = False
        if current_user.role == Roles.ADMIN and target_user.role != Roles.USER:
            allowed = False
        if current_user.role == Roles.SUPER_ADMIN and target_user.role == Roles.SUPER_ADMIN:
            allowed = False
    else:
        # if current_user.role == Roles.ADMIN:  # admins can't change itself
        #     allowed = False
        if current_user.role == Roles.SUPER_ADMIN:  # super_admin can't change itself
            allowed = False

    if not allowed:
        logger.warning(
            f"Permissions: Invalid permission!\n"
            f"{current_user.role}:{current_user.username}:{current_user.id} "
            f"tries to perform an action over "
            f"{target_user.role}:{target_user.username}:{target_user.id}!"
        )

    return allowed
