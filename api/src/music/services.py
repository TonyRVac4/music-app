from api.src.music.utils import download_audio_from_youtube
from api.src.utils.s3_client import S3Client
from redis.asyncio import Redis
from uuid import uuid4
from api.src.music.exceptions import HTTPExceptionOperationNotFound, HTTPExceptionFileNotReady
from fastapi.concurrency import run_in_threadpool


class YoutubeService:
    def __init__(self, redis_client: Redis, s3_client: S3Client):
        self._redis_client = redis_client
        self._s3_client = s3_client

    async def create_operation(self) -> str:
        operation_id = str(uuid4())
        await self._redis_client.rpush(operation_id, '__placeholder__')
        await self._redis_client.expire(operation_id, 600)
        return operation_id

    async def get_operation(self, operation_id: str) -> dict | None:
        data = await self._redis_client.lrange(operation_id, 0, -1)
        if not data:
            raise HTTPExceptionOperationNotFound
        if len(data) != 3:
            raise HTTPExceptionFileNotReady
        return {"title": data[1], "filename": data[2]}

    async def download_audio(self, url: str, operation_id: str) -> None:
        data = await run_in_threadpool(download_audio_from_youtube, url)
        await self._s3_client.upload(file_obj=data["data"], filename=data["filename"])
        await self._redis_client.rpush(operation_id, data["title"], data["filename"])

    async def get_link(self, filename: str) -> str:
        return await self._s3_client.get_link(filename)
