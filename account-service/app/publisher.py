import pika
import json
from datetime import datetime
from decimal import Decimal
import sys
import os
import logging

# Add parent directory to path to import shared module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.events import TransactionEvent

logger = logging.getLogger(__name__)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE")


def get_connection():
    """Create and return RabbitMQ connection"""
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials)
    return pika.BlockingConnection(parameters)


def publish_transaction_event(account_id: int, account_number: str, amount: Decimal, transaction_type: str):
    """Publish transaction event to RabbitMQ"""
    try:
        connection = get_connection()
        channel = connection.channel()

        # Declare queue (idempotent operation)
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)

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
            routing_key=RABBITMQ_QUEUE,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
            ),
        )

        logger.info(f"Published transaction event: {transaction_type} for account {account_id}")
        connection.close()

    except Exception as e:
        logger.error(f"Failed to publish transaction event: {str(e)}")
        # In production, you might want to raise or handle this differently
        raise
