import logging
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import Transaction

logger = logging.getLogger(__name__)

# Fraud detection threshold (simple example)
FRAUD_THRESHOLD = Decimal("10000.00")


def process_transaction(db: Session, account_id: int, account_number: str, amount: Decimal, transaction_type: str):
    """Process a transaction and store it in the database"""

    # Simple fraud detection simulation
    fraud_detected = False
    notes = None

    if amount > FRAUD_THRESHOLD:
        fraud_detected = True
        notes = f"Large transaction detected: {amount} {transaction_type}"
        logger.warning("Fraud alert: Large transaction of %s for account %s", amount, account_id)

    # Create transaction record
    transaction = Transaction(
        account_id=account_id,
        account_number=account_number,
        amount=amount,
        transaction_type=transaction_type,
        fraud_detected=fraud_detected,
        notes=notes,
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    logger.info("Processed transaction %s: %s of %s for account %s", transaction.id, transaction_type, amount, account_id)

    return transaction


def get_transactions(db: Session, account_id: int = None, skip: int = 0, limit: int = 100):
    """Get transaction history"""
    query = db.query(Transaction)

    if account_id:
        query = query.filter(Transaction.account_id == account_id)

    return query.order_by(Transaction.processed_at.desc(), Transaction.id.desc()).offset(skip).limit(limit).all()
