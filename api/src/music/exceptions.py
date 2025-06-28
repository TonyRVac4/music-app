from fastapi import HTTPException, status

HTTPExceptionOperationNotFound = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Operation not found!",
)

HTTPExceptionFileNotReady = HTTPException(
    status_code=status.HTTP_202_ACCEPTED,
    detail="File is not ready yet!",
)
