import json
import os
import sys

import pika
import structlog

# Add parent directory to path to import shared module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.events import TransactionEvent  # pylint: disable=wrong-import-position,wrong-import-order
from shared.logging_config import get_logger  # pylint: disable=wrong-import-position
from app.database import SessionLocal  # pylint: disable=wrong-import-position
from app.service import process_transaction  # pylint: disable=wrong-import-position

logger = get_logger(__name__)


def callback(ch, method, _properties, body):
    """Callback function to process incoming messages"""
    # Extract correlation ID from message headers if available
    correlation_id = "unknown"
    if _properties.headers and "correlation_id" in _properties.headers:
        correlation_id = _properties.headers["correlation_id"]
    
    # Bind correlation ID to context for all logs in this callback
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
    
    try:
        # Parse message
        message_data = json.loads(body)
        event = TransactionEvent(**message_data)

        logger.info(
            "transaction_event_received",
            transaction_type=event.transaction_type,
            account_id=event.account_id,
            account_number=event.account_number,
            amount=str(event.amount),
            correlation_id=correlation_id,
        )

        # Process transaction
        db = SessionLocal()
        try:
            transaction = process_transaction(
                db=db,
                account_id=event.account_id,
                account_number=event.account_number,
                amount=event.amount,
                transaction_type=event.transaction_type,
            )
            logger.info(
                "transaction_processing_successful",
                transaction_id=transaction.id,
                account_id=event.account_id,
                correlation_id=correlation_id,
            )

            # Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except (ValueError, RuntimeError) as e:
            logger.error(
                "transaction_processing_failed",
                account_id=event.account_id,
                account_number=event.account_number,
                amount=str(event.amount),
                transaction_type=event.transaction_type,
                correlation_id=correlation_id,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            # In production, you might want to use a dead letter queue
            # For now, we'll reject and requeue
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        finally:
            db.close()

    except json.JSONDecodeError as e:
        logger.error(
            "message_parse_failed",
            correlation_id=correlation_id,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except (ConnectionError, RuntimeError) as e:
        logger.error(
            "unexpected_callback_error",
            correlation_id=correlation_id,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    finally:
        # Clear context vars after processing
        structlog.contextvars.clear_contextvars()


def start_consumer():
    """Start consuming messages from RabbitMQ"""
    try:
        rabbitmq_host = os.getenv("RABBITMQ_HOST")
        rabbitmq_port_str = os.getenv("RABBITMQ_PORT")
        rabbitmq_user = os.getenv("RABBITMQ_USER")
        rabbitmq_password = os.getenv("RABBITMQ_PASSWORD")
        rabbitmq_queue = os.getenv("RABBITMQ_QUEUE")

        if not all([rabbitmq_host, rabbitmq_port_str, rabbitmq_user, rabbitmq_password, rabbitmq_queue]):
            raise RuntimeError("RabbitMQ environment variables are not set")

        rabbitmq_port = int(rabbitmq_port_str)
        credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_password)
        parameters = pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port, credentials=credentials)

        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        # Declare queue (idempotent operation)
        channel.queue_declare(queue=rabbitmq_queue, durable=True)

        # Set QoS to process one message at a time
        channel.basic_qos(prefetch_count=1)

        # Set up consumer
        channel.basic_consume(queue=rabbitmq_queue, on_message_callback=callback)

        logger.info(
            "rabbitmq_consumer_started",
            queue=rabbitmq_queue,
            host=rabbitmq_host,
            port=rabbitmq_port,
        )
        logger.info("waiting_for_messages")

        # Start consuming
        channel.start_consuming()

    except KeyboardInterrupt:
        logger.info("rabbitmq_consumer_stopping")
        channel.stop_consuming()
        connection.close()
    except (ConnectionError, RuntimeError) as e:
        logger.error(
            "rabbitmq_consumer_error",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        raise
