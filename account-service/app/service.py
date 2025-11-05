from sqlalchemy.orm import Session
from decimal import Decimal
from app.models import Account
from app import publisher
import logging

logger = logging.getLogger(__name__)


def create_account(db: Session, account_number: str):
    """Create a new account"""
    account = Account(account_number=account_number, balance=Decimal("0.00"))
    db.add(account)
    db.commit()
    db.refresh(account)
    logger.info(f"Created account {account.id} with number {account_number}")
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
        return None
    
    account.balance += amount
    db.commit()
    db.refresh(account)
    
    # Publish transaction event
    try:
        publisher.publish_transaction_event(
            account_id=account.id,
            account_number=account.account_number,
            amount=amount,
            transaction_type="deposit"
        )
    except Exception as e:
        logger.error(f"Failed to publish deposit event: {str(e)}")
    
    logger.info(f"Deposited {amount} to account {account_id}")
    return account


def withdraw(db: Session, account_id: int, amount: Decimal):
    """Withdraw funds from account"""
    account = get_account(db, account_id)
    if not account:
        return None
    
    if account.balance < amount:
        raise ValueError("Insufficient funds")
    
    account.balance -= amount
    db.commit()
    db.refresh(account)
    
    # Publish transaction event
    try:
        publisher.publish_transaction_event(
            account_id=account.id,
            account_number=account.account_number,
            amount=amount,
            transaction_type="withdraw"
        )
    except Exception as e:
        logger.error(f"Failed to publish withdraw event: {str(e)}")
    
    logger.info(f"Withdrew {amount} from account {account_id}")
    return account

