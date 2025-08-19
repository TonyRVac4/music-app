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

HTTPExceptionNoPermission = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="You do not have permission to use this operation!",
)

HTTPExceptionInvalidEmailVerification = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Invalid or expired email verification credentials!"
)

HTTPExceptionInactiveUser = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="User account is inactive!",
)
