from fastapi import HTTPException, status


HTTPExceptionEmailNotFound = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Email not found!",
)

HTTPExceptionUserNotFound = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="User not found!",
)

HTTPExceptionUserAlreadyExists = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="User already exists!",
)

HTTPExceptionEmailAlreadyVerified = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Email is already verified!",
)
