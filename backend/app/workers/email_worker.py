from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone

import pika
from sqlalchemy import select

from app.config import settings
from app.database.session import SessionLocal
from app.models import EmailQueue, EmailQueueStatus
from app.services.email_jobs import ensure_queue

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def process_message(body: bytes) -> None:
    payload = json.loads(body.decode("utf-8"))
    email_queue_id = payload["email_queue_id"]

    with SessionLocal() as db:
        job = db.scalars(select(EmailQueue).where(EmailQueue.id == email_queue_id)).one_or_none()
        if job is None:
            logger.warning("Email job %s missing; skipping", email_queue_id)
            return

        logger.info(
            "Simulated email sent to %s for order %s with subject %s",
            payload["recipient_email"],
            payload["order_id"],
            payload["subject"],
        )
        job.status = EmailQueueStatus.sent.value
        job.sent_at = _utcnow()
        job.last_error = None
        db.commit()


def main() -> None:
    while True:
        try:
            connection = pika.BlockingConnection(pika.URLParameters(settings.rabbitmq_url))
            channel = connection.channel()
            ensure_queue(channel)
            channel.basic_qos(prefetch_count=1)

            def callback(ch, method, _properties, body):
                try:
                    process_message(body)
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Email worker failed to process message: %s", exc)
                    try:
                        payload = json.loads(body.decode("utf-8"))
                        with SessionLocal() as db:
                            job = db.scalars(
                                select(EmailQueue).where(EmailQueue.id == payload["email_queue_id"])
                            ).one_or_none()
                            if job is not None:
                                job.status = EmailQueueStatus.failed.value
                                job.last_error = str(exc)
                                db.commit()
                    finally:
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                    return

                ch.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_consume(queue=settings.rabbitmq_queue_name, on_message_callback=callback)
            logger.info("RabbitMQ email worker started on queue %s", settings.rabbitmq_queue_name)
            channel.start_consuming()
        except Exception as exc:  # noqa: BLE001
            logger.exception("RabbitMQ worker connection failed: %s", exc)
            time.sleep(5)


if __name__ == "__main__":
    main()
