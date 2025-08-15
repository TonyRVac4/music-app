import datetime
import uuid
from typing import Annotated

from sqlalchemy import DateTime, text
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
