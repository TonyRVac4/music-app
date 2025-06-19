from fastapi import HTTPException, status


HTTPExceptionInvalidToken = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid Token!",
    headers={"WWW-Authenticate": "Bearer"},
)


HTTPExceptionInvalidLoginCredentials = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid login or password!",
)

HTTPExceptionEmailNotFound = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Email not found!",
)

HTTPExceptionUserNotFound = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="User not found!",
)

HTTPExceptionInactiveUser = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="User account is inactive!",
)

HTTPExceptionNoPermission = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="You do not have permission to use this operation!",
)

HTTPExceptionUserAlreadyExists = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="User already exists!",
)

HTTPExceptionInvalidEmailVerification = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Invalid or expired email verification credentials!"
)

HTTPExceptionEmailAlreadyVerified = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Email is already verified!"
)
