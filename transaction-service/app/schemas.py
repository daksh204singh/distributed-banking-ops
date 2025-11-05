from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class TransactionResponse(BaseModel):
    id: int
    account_id: int
    account_number: str
    amount: Decimal
    transaction_type: str
    processed_at: datetime
    fraud_detected: bool
    notes: Optional[str] = None

    class Config:
        from_attributes = True
