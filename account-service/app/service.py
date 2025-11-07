from decimal import Decimal

from sqlalchemy.orm import Session

from shared.logging_config import get_logger
from app import publisher
from app.models import Account

logger = get_logger(__name__)


def create_account(db: Session, account_number: str):
    """Create a new account"""
    account = Account(account_number=account_number, balance=Decimal("0.00"))
    db.add(account)
    db.commit()
    db.refresh(account)
    logger.info(
        "account_created",
        account_id=account.id,
        account_number=account_number,
        initial_balance=str(account.balance),
    )
    return account


def get_account(db: Session, account_id: int):
    """Get account by ID"""
    return db.query(Account).filter(Account.id == account_id).first()


def get_account_by_number(db: Session, account_number: str):
    """Get account by account number"""
    return db.query(Account).filter(Account.account_number == account_number).first()


def deposit(db: Session, account_id: int, amount: Decimal):
    """Deposit funds to account"""
    account = get_account(db, account_id)
    if not account:
        logger.warning("deposit_failed", reason="account_not_found", account_id=account_id)
        return None

    old_balance = account.balance
    account.balance += amount
    db.commit()
    db.refresh(account)

    # Publish transaction event
    try:
        publisher.publish_transaction_event(
            account_id=account.id, account_number=account.account_number, amount=amount, transaction_type="deposit"
        )
        logger.info(
            "deposit_successful",
            account_id=account_id,
            account_number=account.account_number,
            amount=str(amount),
            old_balance=str(old_balance),
            new_balance=str(account.balance),
        )
    except (ConnectionError, ValueError, RuntimeError) as e:
        logger.error(
            "deposit_event_publish_failed",
            account_id=account_id,
            account_number=account.account_number,
            amount=str(amount),
            old_balance=str(old_balance),
            new_balance=str(account.balance),
            error=str(e),
            error_type=type(e).__name__,
        )

    return account


def withdraw(db: Session, account_id: int, amount: Decimal):
    """Withdraw funds from account"""
    account = get_account(db, account_id)
    if not account:
        logger.warning("withdraw_failed", reason="account_not_found", account_id=account_id)
        return None

    if account.balance < amount:
        logger.warning(
            "withdraw_failed",
            reason="insufficient_funds",
            account_id=account_id,
            account_number=account.account_number,
            requested_amount=str(amount),
            current_balance=str(account.balance),
        )
        raise ValueError("Insufficient funds")

    old_balance = account.balance
    account.balance -= amount
    db.commit()
    db.refresh(account)

    # Publish transaction event
    try:
        publisher.publish_transaction_event(
            account_id=account.id, account_number=account.account_number, amount=amount, transaction_type="withdraw"
        )
        logger.info(
            "withdraw_successful",
            account_id=account_id,
            account_number=account.account_number,
            amount=str(amount),
            old_balance=str(old_balance),
            new_balance=str(account.balance),
        )
    except (ConnectionError, ValueError, RuntimeError) as e:
        logger.error(
            "withdraw_event_publish_failed",
            account_id=account_id,
            account_number=account.account_number,
            amount=str(amount),
            old_balance=str(old_balance),
            new_balance=str(account.balance),
            error=str(e),
            error_type=type(e).__name__,
        )

    return account
