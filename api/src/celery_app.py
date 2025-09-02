from celery import Celery

from api.src.infrastructure.settings import settings

app = Celery(
    "music-app",
    broker=settings.redis.broker_url,
    backend=settings.redis.broker_url,
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],  # Ignore other content
    result_serializer="json",
    result_expires=900, # result TTL 15 min
    timezone="UTC",
    enable_utc=True,
)

# Automatically discover tasks in files named 'tasks.py'
app.autodiscover_tasks(
    lambda: [
        "api.src.domain.auth",
        "api.src.domain.users",
        "api.src.domain.music",
    ]
)
