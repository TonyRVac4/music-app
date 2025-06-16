from api.src.database.repository import SQLAlchemyRepository
from api.src.database.models import UserModel


class UserRepository(SQLAlchemyRepository[UserModel]):
    model = UserModel
