from ..exceptions import AppException


class ConstraintViolation(AppException):
    """
    Raised when a constraint is violated in the database.
    """

class EntityNotFound(AppException):
    """
    Raised when a entity cannot be found.
    """