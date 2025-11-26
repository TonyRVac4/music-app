from typing import Annotated

from fastapi import APIRouter, status, Query

from api.src.domain.music.schemas import FileInfoResponse, OperationId
from api.src.infrastructure.app import app
from api.src.domain.music.tasks import download_audio


router = APIRouter(prefix="/youtube", tags=["Youtube"])


@router.post(
    "/download",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=OperationId,
)
async def start_downloading(
    url: Annotated[str, Query(pattern="^https://www.youtube.com/watch")],
) -> dict:
    task = download_audio.delay(url)
    return {"operation_id": task.id}


@router.get(
    "/download",
    status_code=status.HTTP_200_OK,
    response_model=FileInfoResponse,
)
async def get_downloaded_file(
    operation_id: str,
) -> dict:
    return await app.youtube_service.get_operation(operation_id)


# @router.post("/save")
# async def save_downloaded_file_to_db(
#         data: SongInfo,
#         user: Annotated[BaseUserInfo, Depends(get_current_active_user)],
# ):
#     # check if file exist in temporary s3 bucket
#     # move it to permanent bucket and remove form temporary
#     # save data in db
#     ...
