from api.src.celery_app import app as celery_app

from api.src.domain.music.utils import (
    download_audio_from_youtube,
    get_audio_data_from_youtube,
)

from api.src.infrastructure.settings import settings
from api.src.infrastructure.app import app as app_container
from api.src.domain.music.schemas import FileDTO


@celery_app.task(bind=True)
def download_audio(self, url: str) -> None:
    operation_id = f"celery-task-{self.request.id}"

    with app_container.redis_client(settings.redis.app_url) as client:
        # создать операцию в redis
        client.rpush(operation_id, "__placeholder__")
        client.expire(operation_id, 1800)

    try:
        # получить метаданные данные о видео
        metadata: FileDTO = get_audio_data_from_youtube(url)

        # проверить нет ли нарушения ограничения на продолжительность скачиваемого ресурса
        if not metadata.duration > settings.youtube.video_duration_constraint:
            # если файл с таким именем не существует в s3, скачать и загрузить в s3
            if not app_container.s3_client.check(metadata.filename):
                new_file: FileDTO = download_audio_from_youtube(url)
                app_container.s3_client.upload(
                    file_obj=new_file.data, filename=new_file.filename,
                )

            # получаем ссылку на видео в хранилище
            link = app_container.s3_client.get_link(metadata.filename, expires_in=1800)
            with app_container.redis_client(settings.redis.app_url) as client:
                # сохраняем полученные данные в редис по id операции
                client.rpush(
                    operation_id,
                    metadata.title,
                    metadata.filename,
                    str(metadata.duration).replace(".", ":"),
                    link,
                )
        else:
            with app_container.redis_client(settings.redis.app_url) as client:
                # сохраняем данные в редис по id операции
                client.rpush(operation_id, "__too_long__")
                client.expire(operation_id, 300)
    except Exception as e:
        with app_container.redis_client(settings.redis.app_url) as client:
            client.rpush(operation_id, "__exception__", str(e))
        raise
