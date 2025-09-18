from celery import Celery
from celery.schedules import crontab
import os
from .config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND, DEFAULT_URLS

app = Celery(
    "lab3",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["app.tasks"],
)

app.conf.update(
    timezone=os.getenv("TZ", "Europe/Helsinki"),
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_time_limit=300,
    task_track_started=True,
    result_expires=3600,

    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",
)

app.conf.beat_schedule = {
    "parse-default-urls-hourly": {
        "task": "app.tasks.parse_many_task",
        "schedule": crontab(minute=0),
        "args": [DEFAULT_URLS],
    },
}