from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from typing import Optional


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
