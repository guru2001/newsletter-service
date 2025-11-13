from celery import Celery
from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

celery_app = Celery(
    "newsletter_service",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_ignore_result=True,  # Don't wait for results
    task_acks_late=True,  # Acknowledge tasks after execution
    broker_connection_retry_on_startup=True,
    # Connection resilience settings
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    broker_connection_timeout=30,
    # Heartbeat settings
    worker_send_task_events=True,
    worker_prefetch_multiplier=1,  # Process one task at a time
    # Task settings
    task_reject_on_worker_lost=True,  # Reject tasks if worker dies
    task_acks_on_failure_or_timeout=True,
)

