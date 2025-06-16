from fastapi import HTTPException
from starlette import status


HTTPExceptionInvalidToken = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid Token!",
    headers={"WWW-Authenticate": "Bearer"},
)


HTTPExceptionInvalidLoginCredentials = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid login or password!",
)


HTTPExceptionInactiveUser = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="User account is inactive!",
)

HTTPExceptionUserAlreadyExists = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="User already exists!",
)
