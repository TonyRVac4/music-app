from fastapi import HTTPException

HTTPExceptionInternalServerError = HTTPException(
        status_code=500,
        detail="Something went wrong! Developers has already been notified and will fix this asap!",
)
