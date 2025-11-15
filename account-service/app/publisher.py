import json
import os
from datetime import datetime
from decimal import Decimal

import pika
import structlog

from shared.events import TransactionEvent
from shared.logging_config import get_logger
from shared.prometheus import record_publish

logger = get_logger(__name__)


def get_connection():
    """Create and return RabbitMQ connection"""
    rabbitmq_host = os.getenv("RABBITMQ_HOST")
    rabbitmq_port_str = os.getenv("RABBITMQ_PORT")
    rabbitmq_user = os.getenv("RABBITMQ_USER")
    rabbitmq_password = os.getenv("RABBITMQ_PASSWORD")

    if not all([rabbitmq_host, rabbitmq_port_str, rabbitmq_user, rabbitmq_password]):
        raise RuntimeError("RabbitMQ environment variables are not set")

    rabbitmq_port = int(rabbitmq_port_str)
    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_password)
    parameters = pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port, credentials=credentials)
    return pika.BlockingConnection(parameters)


def publish_transaction_event(account_id: int, account_number: str, amount: Decimal, transaction_type: str):
    """Publish transaction event to RabbitMQ"""
    # Get correlation ID from context if available
    context = structlog.contextvars.get_contextvars()
    correlation_id = context.get("correlation_id", "unknown")

    try:
        rabbitmq_queue = os.getenv("RABBITMQ_QUEUE")
        if not rabbitmq_queue:
            raise RuntimeError("RABBITMQ_QUEUE environment variable is not set")

        connection = get_connection()
        channel = connection.channel()

        # Declare queue (idempotent operation)
        channel.queue_declare(queue=rabbitmq_queue, durable=True)

        # Create event
        event = TransactionEvent(
            account_id=account_id,
            account_number=account_number,
            amount=amount,
            transaction_type=transaction_type,
            timestamp=datetime.utcnow(),
        )

        # Publish message
        message = json.dumps(event.model_dump(), default=str)
        channel.basic_publish(
            exchange="",
            routing_key=rabbitmq_queue,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
                headers={"correlation_id": correlation_id},  # Add correlation ID for tracing
            ),
        )

        record_publish(exchange="", routing_key=rabbitmq_queue)

        logger.info(
            "transaction_event_published",
            transaction_type=transaction_type,
            account_id=account_id,
            account_number=account_number,
            amount=str(amount),
            queue=rabbitmq_queue,
            correlation_id=correlation_id,
        )
        connection.close()

    except (ConnectionError, ValueError, RuntimeError) as e:
        logger.error(
            "transaction_event_publish_failed",
            transaction_type=transaction_type,
            account_id=account_id,
            account_number=account_number,
            amount=str(amount),
            correlation_id=correlation_id,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        # In production, you might want to raise or handle this differently
        raise
