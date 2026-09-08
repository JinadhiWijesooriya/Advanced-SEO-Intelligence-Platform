from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "seo_platform_workers",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

celery_app.conf.beat_schedule = {
    "process-scheduled-scans": {
        "task": "app.workers.tasks.process_scheduled_scans",
        "schedule": 60.0, # Every minute
    },
}
