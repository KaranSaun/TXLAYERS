from celery import Celery

# Hardcoded Redis URL
REDIS_URL = "redis://redis:6379/0"

celery_app = Celery(
    "texlayer_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "app.workers.pipeline"
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3300,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=10,
)
