from typing import Any


class AppException(Exception):
    """
    The base exception class for the application.
    """

    message: str
    details: Any

    def __init__(self, message: str, details: Any = None, *args) -> None:
        super().__init__(*args)
        self.message = message
        self.details = details
