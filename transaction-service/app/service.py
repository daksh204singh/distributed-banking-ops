from decimal import Decimal

from sqlalchemy.orm import Session

from shared.logging_config import get_logger, mask_account_number, mask_amount
from app.models import Transaction

logger = get_logger(__name__)

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
        logger.warning(
            "fraud_alert",
            reason="large_transaction_detected",
            account_id=account_id,
            account_number=mask_account_number(account_number),
            amount=mask_amount(str(amount)),
            transaction_type=transaction_type,
            threshold=mask_amount(str(FRAUD_THRESHOLD)),
        )

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

    logger.info(
        "transaction_processed",
        transaction_id=transaction.id,
        account_id=account_id,
        account_number=mask_account_number(account_number),
        amount=mask_amount(str(amount)),
        transaction_type=transaction_type,
        fraud_detected=fraud_detected,
    )

    return transaction


def get_transactions(db: Session, account_id: int = None, skip: int = 0, limit: int = 100):
    """Get transaction history"""
    query = db.query(Transaction)

    if account_id:
        query = query.filter(Transaction.account_id == account_id)

    return query.order_by(Transaction.processed_at.desc(), Transaction.id.desc()).offset(skip).limit(limit).all()
