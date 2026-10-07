"""Celery application configuration with durable RabbitMQ broker settings."""
import os
from celery import Celery

broker_url = os.environ.get("RABBITMQ_URL", "amqp://rag:rabbitmq-local-pass@localhost:5672//")
celery_app = Celery("logistics_rag_workers", broker=broker_url)
celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_default_queue="ingestion",
    task_create_missing_queues=True,
)
