import pika
import json
import logging
import os
import sys

# Add parent directory to path to import shared module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from app.database import SessionLocal
from app.service import process_transaction
from shared.events import TransactionEvent

logger = logging.getLogger(__name__)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE")


def callback(ch, method, properties, body):
    """Callback function to process incoming messages"""
    try:
        # Parse message
        message_data = json.loads(body)
        event = TransactionEvent(**message_data)
        
        logger.info(f"Received transaction event: {event.transaction_type} for account {event.account_id}")
        
        # Process transaction
        db = SessionLocal()
        try:
            transaction = process_transaction(
                db=db,
                account_id=event.account_id,
                account_number=event.account_number,
                amount=event.amount,
                transaction_type=event.transaction_type
            )
            logger.info(f"Successfully processed transaction {transaction.id}")
            
            # Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            logger.error(f"Error processing transaction: {str(e)}")
            # In production, you might want to use a dead letter queue
            # For now, we'll reject and requeue
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        finally:
            db.close()
            
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse message: {str(e)}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        logger.error(f"Unexpected error in callback: {str(e)}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def start_consumer():
    """Start consuming messages from RabbitMQ"""
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials
        )
        
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        
        # Declare queue (idempotent operation)
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        
        # Set QoS to process one message at a time
        channel.basic_qos(prefetch_count=1)
        
        # Set up consumer
        channel.basic_consume(
            queue=RABBITMQ_QUEUE,
            on_message_callback=callback
        )
        
        logger.info(f"Started consuming messages from queue: {RABBITMQ_QUEUE}")
        logger.info("Waiting for messages. To exit press CTRL+C")
        
        # Start consuming
        channel.start_consuming()
        
    except KeyboardInterrupt:
        logger.info("Stopping consumer...")
        channel.stop_consuming()
        connection.close()
    except Exception as e:
        logger.error(f"Error in consumer: {str(e)}")
        raise

