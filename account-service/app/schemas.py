from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class AccountCreate(BaseModel):
    account_number: str = Field(..., description="Unique account number")


class AccountResponse(BaseModel):
    id: int
    account_number: str
    balance: Decimal
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DepositRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Deposit amount (must be positive)")


class WithdrawRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Withdrawal amount (must be positive)")
