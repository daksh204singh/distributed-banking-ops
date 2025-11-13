from __future__ import annotations

from typing import Iterable, Tuple

from prometheus_client import Counter, Histogram

MESSAGES_PUBLISHED_TOTAL = Counter(
    "rabbitmq_messages_published_total",
    "Total number of messages published to RabbitMQ",
    ["exchange", "routing_key"],
)

MESSAGES_CONSUMED_TOTAL = Counter(
    "rabbitmq_messages_consumed_total",
    "Total number of messages consumed by this service",
    ["queue", "status"],
)

MESSAGE_PROCESSING_DURATION = Histogram(
    "rabbitmq_message_processing_duration_seconds",
    "Time taken to process a consumed message (seconds)",
    ["queue", "status"],
    buckets=(0.1, 0.25, 0.5, 1, 2, 5, 10),
)


def register_rabbitmq_metrics(
    exchanges: Iterable[str] | None = None,
    routing_keys: Iterable[str] | None = None,
    queues: Iterable[str] | None = None,
    statuses: Iterable[str] | None = None,
) -> None:
    if exchanges is not None or routing_keys is not None:
        exchange_values: Tuple[str, ...] = tuple(exchanges or ("",))
        routing_key_values: Tuple[str, ...] = tuple(routing_keys or ("",))
        for exchange in exchange_values:
            for routing_key in routing_key_values:
                MESSAGES_PUBLISHED_TOTAL.labels(exchange=exchange or "", routing_key=routing_key or "")

    if queues is not None or statuses is not None:
        queue_values: Tuple[str, ...] = tuple(queues or ("",))
        status_values: Tuple[str, ...] = tuple(statuses or ("success", "failed"))
        for queue in queue_values:
            for status in status_values:
                MESSAGES_CONSUMED_TOTAL.labels(queue=queue or "", status=status or "")
                MESSAGE_PROCESSING_DURATION.labels(queue=queue or "", status=status or "")


def record_publish(exchange: str, routing_key: str) -> None:
    MESSAGES_PUBLISHED_TOTAL.labels(exchange=exchange or "", routing_key=routing_key or "").inc()


def record_consume(queue: str, status: str, duration: float) -> None:
    normalized_queue = queue or ""
    normalized_status = status or ""
    MESSAGES_CONSUMED_TOTAL.labels(queue=normalized_queue, status=normalized_status).inc()
    MESSAGE_PROCESSING_DURATION.labels(queue=normalized_queue, status=normalized_status).observe(max(duration, 0))


