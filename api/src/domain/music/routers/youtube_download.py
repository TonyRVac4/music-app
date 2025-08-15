from typing import Annotated

from fastapi import APIRouter, Depends, BackgroundTasks, status, Query

from api.src.domain.music.schemas import FileInfoOut, OperationId
# from api.src.dependencies.auth_deps import get_current_active_user
# from api.src.users.schemas import BaseUserInfo
from api.src.infrastructure.app import app

router = APIRouter(prefix="/youtube", tags=["Youtube"])


@router.post(
    "/download",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=OperationId,
)
async def start_downloading(
        url: Annotated[str, Query(pattern='^https://www.youtube.com/watch')],
        background_tasks: BackgroundTasks,
        # user: Annotated[BaseUserInfo, Depends(get_current_active_user)],
) -> OperationId:
    operation_id: str = await app.yt_service.create_operation()
    background_tasks.add_task(app.yt_service.download_audio, url, operation_id)
    return {"operation_id": operation_id}


@router.get(
    "/download",
    status_code=status.HTTP_200_OK,
    response_model=FileInfoOut,
)
async def get_check_downloaded_file(
        operation_id: str,
        # user: Annotated[BaseUserInfo, Depends(get_current_active_user)],
) -> FileInfoOut:
    return await app.yt_service.get_operation(operation_id)


# @router.post("/save")
# async def save_downloaded_file_to_db(
#         data: SongInfo,
#         user: Annotated[BaseUserInfo, Depends(get_current_active_user)],
# ):
#     # check if file exist in temporary s3 bucket
#     # move it to permanent bucket and remove form temporary
#     # save data in db
#     ...
