from celery import Celery

from app.config import get_config

config = get_config()

celery_app = Celery(
    "quantfox",
    broker=config.celery.broker_url,
    backend=config.celery.result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    result_expires=3600,
)

# Import tasks to register them
from app import tasks  # noqa: F401, E402
