import uuid
import datetime
from sqlalchemy import VARCHAR, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from api.src.infrastructure.database.models import Base, int_pk


class SQLAlchemyRefreshTokenModel(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int_pk]
    token_id: Mapped[str] = mapped_column(VARCHAR, unique=True, nullable=False)
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
