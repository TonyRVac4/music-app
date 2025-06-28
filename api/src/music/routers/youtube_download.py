from typing import Annotated

from fastapi import APIRouter, Depends, BackgroundTasks, status

from api.src.music.schemas import SongInfoOut, OperationId
# from api.src.dependencies.auth_deps import get_current_active_user
# from api.src.users.schemas import BaseUserInfo

from api.src.music.dependencies import get_youtube_service, YoutubeService

router = APIRouter(prefix="/youtube", tags=["Youtube"])


@router.post(
    "/download",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=OperationId,
)
async def start_downloading(
        url: str,
        background_tasks: BackgroundTasks,
        # user: Annotated[BaseUserInfo, Depends(get_current_active_user)],
        yt_service: Annotated[YoutubeService, Depends(get_youtube_service)],
) -> OperationId:
    operation_id: str = await yt_service.create_operation()
    background_tasks.add_task(yt_service.download_audio, url, operation_id)
    return {"operation_id": operation_id}


@router.get(
    "/download",
    status_code=status.HTTP_200_OK,
    response_model=SongInfoOut,
)
async def get_check_downloaded_file(
        operation_id: str,
        # user: Annotated[BaseUserInfo, Depends(get_current_active_user)],
        yt_service: Annotated[YoutubeService, Depends(get_youtube_service)],
) -> SongInfoOut:
    song_info = await yt_service.get_operation(operation_id)
    song_info["link"] = await yt_service.get_link(song_info["filename"])
    return song_info


# @router.post("/save")
# async def save_downloaded_file_to_db(
#         data: SongInfo,
#         user: Annotated[BaseUserInfo, Depends(get_current_active_user)],
# ):
#     # check if file exist in temporary s3 bucket
#     # move it to permanent bucket and remove form temporary
#     # save data in db
#     ...
