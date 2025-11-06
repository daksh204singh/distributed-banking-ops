import json
import logging
import os
import sys

import pika

# Add parent directory to path to import shared module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.events import TransactionEvent  # pylint: disable=wrong-import-position,wrong-import-order
from app.database import SessionLocal  # pylint: disable=wrong-import-position
from app.service import process_transaction  # pylint: disable=wrong-import-position

logger = logging.getLogger(__name__)


def callback(ch, method, _properties, body):
    """Callback function to process incoming messages"""
    try:
        # Parse message
        message_data = json.loads(body)
        event = TransactionEvent(**message_data)

        logger.info("Received transaction event: %s for account %s", event.transaction_type, event.account_id)

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
            logger.info("Successfully processed transaction %s", transaction.id)

            # Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except (ValueError, RuntimeError) as e:
            logger.error("Error processing transaction: %s", str(e))
            # In production, you might want to use a dead letter queue
            # For now, we'll reject and requeue
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        finally:
            db.close()

    except json.JSONDecodeError as e:
        logger.error("Failed to parse message: %s", str(e))
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except (ConnectionError, RuntimeError) as e:
        logger.error("Unexpected error in callback: %s", str(e))
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


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

        logger.info("Started consuming messages from queue: %s", rabbitmq_queue)
        logger.info("Waiting for messages. To exit press CTRL+C")

        # Start consuming
        channel.start_consuming()

    except KeyboardInterrupt:
        logger.info("Stopping consumer...")
        channel.stop_consuming()
        connection.close()
    except (ConnectionError, RuntimeError) as e:
        logger.error("Error in consumer: %s", str(e))
        raise
