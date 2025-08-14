from sqlalchemy import VARCHAR, BOOLEAN, text, Enum
from sqlalchemy.orm import Mapped, mapped_column

from api.src.database.models import Base, uuid_pk
from api.src.database.enums import Roles


class SQLAlchemyUserModel(Base):
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
