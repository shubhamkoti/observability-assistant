from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import pika
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import settings
from app.models import EmailQueue, EmailQueueStatus


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _connection() -> pika.BlockingConnection:
    params = pika.URLParameters(settings.rabbitmq_url)
    return pika.BlockingConnection(params)


def ensure_queue(channel: pika.adapters.blocking_connection.BlockingChannel) -> None:
    channel.queue_declare(queue=settings.rabbitmq_queue_name, durable=True)


def publish_email_job(db: Session, email_job: EmailQueue) -> bool:
    if email_job.status != EmailQueueStatus.pending.value:
        return False

    payload: dict[str, Any] = {
        "email_queue_id": email_job.id,
        "user_id": email_job.user_id,
        "order_id": email_job.order_id,
        "payment_id": email_job.payment_id,
        "recipient_email": email_job.recipient_email,
        "subject": email_job.subject,
        "body": email_job.body,
        "from_email": settings.email_from_address,
    }

    connection = _connection()
    try:
        channel = connection.channel()
        ensure_queue(channel)
        channel.basic_publish(
            exchange="",
            routing_key=settings.rabbitmq_queue_name,
            body=json.dumps(payload),
            properties=pika.BasicProperties(delivery_mode=2),
        )
    finally:
        connection.close()

    db.execute(
        update(EmailQueue)
        .where(
            EmailQueue.id == email_job.id,
            EmailQueue.status == EmailQueueStatus.pending.value,
        )
        .values(
            status=EmailQueueStatus.published.value,
            published_at=_utcnow(),
            last_error=None,
        )
    )
    db.commit()
    db.refresh(email_job)
    return True


def publish_pending_email_for_payment(db: Session, payment_id: int) -> bool:
    email_job = db.scalars(
        select(EmailQueue).where(
            EmailQueue.payment_id == payment_id,
            EmailQueue.status == EmailQueueStatus.pending.value,
        )
    ).one_or_none()
    if email_job is None:
        return False
    return publish_email_job(db, email_job)
