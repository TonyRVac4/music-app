from fastapi import HTTPException, status
from api.src.infrastructure.settings import settings

HTTPExceptionOperationNotFound = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Operation not found!",
)

HTTPExceptionFileNotReady = HTTPException(
    status_code=status.HTTP_202_ACCEPTED,
    detail="File is not ready yet!",
)

HTTPExceptionVideoIsTooLong = HTTPException(
    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    detail=f"Video duration exceeds the maximum allowed length of {settings.app.video_duration_constraint} minutes!"
)