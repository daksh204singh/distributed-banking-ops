from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean
from sqlalchemy.sql import func

from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, nullable=False, index=True)
    account_number = Column(String, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    transaction_type = Column(String, nullable=False)  # "deposit" or "withdraw"
    processed_at = Column(DateTime(timezone=True), server_default=func.now())  # pylint: disable=not-callable
    fraud_detected = Column(Boolean, default=False)
    notes = Column(String, nullable=True)
