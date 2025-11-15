from __future__ import annotations

from decimal import Decimal
from typing import Iterable, Union

from fastapi import FastAPI
from prometheus_client import Counter, Histogram

TRANSACTIONS_TOTAL = Counter(
    "transaction_service_transactions_total",
    "Total transaction processing attempts grouped by type and outcome",
    ["type", "status"],
)

TRANSACTION_AMOUNT = Histogram(
    "transaction_service_transaction_amount",
    "Observed transaction amounts grouped by type",
    ["type"],
    buckets=[10, 50, 100, 500, 1000, 5000, 10000],
)

FRAUD_TRANSACTIONS_TOTAL = Counter(
    "transaction_service_fraud_transactions_total",
    "Total number of transactions flagged as fraud",
    ["type", "reason"],
)


def _to_float(amount: Union[Decimal, float, int]) -> float | None:
    if amount is None:
        return None
    try:
        return float(amount)
    except (TypeError, ValueError):
        return None


def record_transaction_success(transaction_type: str, amount: Union[Decimal, float, int]) -> None:
    TRANSACTIONS_TOTAL.labels(type=transaction_type, status="success").inc()
    value = _to_float(amount)
    if value is not None:
        TRANSACTION_AMOUNT.labels(type=transaction_type).observe(value)


def record_transaction_failure(transaction_type: str) -> None:
    TRANSACTIONS_TOTAL.labels(type=transaction_type, status="failed").inc()


def record_fraudulent_transaction(transaction_type: str, reason: str) -> None:
    FRAUD_TRANSACTIONS_TOTAL.labels(type=transaction_type, reason=reason).inc()


def register_transaction_metrics(
    app: FastAPI,
    transaction_types: Iterable[str] | None = None,
    fraud_reasons: Iterable[str] | None = None,
) -> None:
    if getattr(app.state, "transaction_metrics_registered", False):
        return

    app.state.transaction_metrics_registered = True

    types = tuple(transaction_types or ("deposit", "withdraw"))
    statuses = ("success", "failed")
    reasons = tuple(fraud_reasons or ("large_transaction_detected",))

    for transaction_type in types:
        for status in statuses:
            TRANSACTIONS_TOTAL.labels(type=transaction_type, status=status)
        TRANSACTION_AMOUNT.labels(type=transaction_type)

    for transaction_type in types:
        for reason in reasons:
            FRAUD_TRANSACTIONS_TOTAL.labels(type=transaction_type, reason=reason)
