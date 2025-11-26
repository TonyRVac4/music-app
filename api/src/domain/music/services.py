from typing import Callable, AsyncContextManager

from redis import Redis

from api.src.domain.music.exceptions import (
    HTTPExceptionOperationNotFound,
    HTTPExceptionFileNotReady,
    HTTPExceptionVideoIsTooLong,
)
from api.src.domain.exceptions import HTTPExceptionInternalServerError
from api.src.infrastructure.settings import settings


class YoutubeService:
    def __init__(
        self,
        redis_client: Callable[..., AsyncContextManager[Redis]],
    ):
        self._redis_client = redis_client

    async def get_operation(self, operation_id: str) -> dict | None:
        formated_operation_id = f"celery-task-{operation_id}"

        async with self._redis_client(settings.redis.app_url) as client:
            is_exist = await client.exists(formated_operation_id)
            if not is_exist:
                raise HTTPExceptionOperationNotFound
            data = await client.lrange(formated_operation_id, 0, -1)

        if len(data) == 1:
            raise HTTPExceptionFileNotReady
        elif data[1] == "__too_long__":
            raise HTTPExceptionVideoIsTooLong
        elif data[1] == "__exception__":
            raise HTTPExceptionInternalServerError
        else:
            return {
                "title": data[1],
                "filename": data[2],
                "duration": data[3],
                "link": data[4],
            }
