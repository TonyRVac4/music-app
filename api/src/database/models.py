import datetime
import uuid
import enum
from typing import Annotated

from sqlalchemy import VARCHAR, DateTime, BOOLEAN, Enum, text
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy.dialects.postgresql import UUID


uuid_pk = Annotated[
    uuid.UUID,
    mapped_column(
        UUID(as_uuid=True),  # as_uuid=True - алхимия возвращает как объект uuid.UUID, по умолчанию str
        primary_key=True,
        nullable=False,
    ),
]
int_pk = Annotated[int, mapped_column(primary_key=True, autoincrement=True, nullable=False)]


class Roles(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    USER = "USER"


class Base(DeclarativeBase):
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', now())"),
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("TIMEZONE('utc', now())"),
        onupdate=datetime.datetime.utcnow(),
    )


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[uuid_pk]
    username: Mapped[str] = mapped_column(VARCHAR(32), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(VARCHAR(64), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(VARCHAR(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(BOOLEAN, server_default=text("TRUE"), nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(BOOLEAN, server_default=text("FALSE"), nullable=False)
    role: Mapped[Roles] = mapped_column(
        Enum(
            Roles,
            name="roles",
            # native_enum=False указывает не создавать Enum на уровне СУБД (хранится как varchar)
        ),
        server_default=text("'USER'::roles"),
        nullable=False,
    )
