"""
Shared event schemas and constants for microservices communication
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel


class TransactionType(str, Enum):
    """Transaction type enumeration"""

    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"


class TransactionEvent(BaseModel):
    """Standard transaction event schema"""

    account_id: int
    account_number: str
    amount: Decimal
    transaction_type: str  # "deposit" or "withdraw"
    timestamp: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "account_id": 1,
                "account_number": "ACC123456",
                "amount": 100.50,
                "transaction_type": "deposit",
                "timestamp": "2024-01-01T12:00:00",
            }
        }


# RabbitMQ queue names
QUEUE_NAMES = {"TRANSACTION_CREATED": "transaction.created"}
