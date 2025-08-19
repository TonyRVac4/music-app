from uuid import uuid4

from fastapi.concurrency import run_in_threadpool

from api.src.domain.music.utils import download_audio_from_youtube, get_audio_data_from_youtube
from api.src.domain.music.exceptions import (HTTPExceptionOperationNotFound, HTTPExceptionFileNotReady,
                                             HTTPExceptionVideoIsTooLong)
from api.src.infrastructure.s3_client import S3Client
from api.src.infrastructure.settings import settings

from .schemas import FileDTO


class YoutubeService:
    def __init__(
            self,
            s3_client: S3Client,
            redis_client,
    ):
        self._s3_client = s3_client
        self._redis_client = redis_client

    async def create_operation(self) -> str:
        operation_id = str(uuid4())

        async with self._redis_client as client:
            await client.rpush(operation_id, '__placeholder__')
            await client.expire(operation_id, 600)

        return operation_id

    async def get_operation(self, operation_id: str) -> dict | None:
        async with self._redis_client() as client:
            data = await client.lrange(operation_id, 0, -1)

        if not data:
            raise HTTPExceptionOperationNotFound
        if len(data) == 1:
            raise HTTPExceptionFileNotReady
        if len(data) == 2:  # 2nd is __too_long__
            raise HTTPExceptionVideoIsTooLong
        return {"title": data[1], "filename": data[2], "duration": data[3], "link": data[4]}

    async def download_audio(self, url: str, operation_id: str) -> None:
        metadata: FileDTO = await run_in_threadpool(get_audio_data_from_youtube, url)
        # добавить celery
        # ограничение на продолжительность скачиваемого ресурса
        async with self._redis_client() as client:
            if metadata.duration > settings.app.video_duration_constraint:
                await client.rpush(operation_id, "__too_long__")
                await client.expire(operation_id, 100)
            else:
                # если файл с таким именем не существует в s3, скачать и загрузить
                if not await self._s3_client.check(metadata.filename):
                    new_file: FileDTO = await run_in_threadpool(download_audio_from_youtube, url)
                    await self._s3_client.upload(file_obj=new_file.data, filename=new_file.filename)

                link = await self._s3_client.get_link(metadata.filename)
                await client.rpush(
                    operation_id,
                    metadata.title, metadata.filename, metadata.duration, link,
                )
