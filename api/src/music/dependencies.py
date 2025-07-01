from typing import Annotated
from fastapi import Depends

from api.src.music.services import YoutubeService
from api.src.dependencies.db_deps import S3Client, get_async_s3_client
from api.src.dependencies.db_deps import Redis, get_async_redis_client


async def get_youtube_service(
        redis: Annotated[Redis, Depends(get_async_redis_client)],
        s3: Annotated[S3Client, Depends(get_async_s3_client)],
) -> YoutubeService:
    return YoutubeService(redis_client=redis, s3_client=s3)
