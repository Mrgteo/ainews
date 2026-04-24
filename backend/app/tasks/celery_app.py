from celery import Celery
from app.config import settings

celery_app = Celery(
    "sentiment_monitor",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    worker_prefetch_multiplier=1,
)

celery_app.autodiscover_tasks(["app.tasks"])
