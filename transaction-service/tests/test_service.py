import pytest
from decimal import Decimal

from app import service
from app.models import Transaction


def test_process_transaction_deposit(test_db):
    """Test processing a deposit transaction"""
    transaction = service.process_transaction(
        db=test_db,
        account_id=1,
        account_number="ACC001",
        amount=Decimal("500.00"),
        transaction_type="deposit",
    )
    
    assert transaction.account_id == 1
    assert transaction.account_number == "ACC001"
    assert transaction.amount == Decimal("500.00")
    assert transaction.transaction_type == "deposit"
    assert transaction.fraud_detected is False


def test_process_transaction_withdraw(test_db):
    """Test processing a withdrawal transaction"""
    transaction = service.process_transaction(
        db=test_db,
        account_id=2,
        account_number="ACC002",
        amount=Decimal("200.00"),
        transaction_type="withdraw",
    )
    
    assert transaction.transaction_type == "withdraw"
    assert transaction.fraud_detected is False


def test_process_transaction_fraud_detection(test_db):
    """Test fraud detection for large transactions"""
    transaction = service.process_transaction(
        db=test_db,
        account_id=3,
        account_number="ACC003",
        amount=Decimal("15000.00"),
        transaction_type="deposit",
    )
    
    assert transaction.fraud_detected is True
    assert transaction.notes is not None
    assert "Large transaction" in transaction.notes


def test_process_transaction_no_fraud_small_amount(test_db):
    """Test that small transactions don't trigger fraud detection"""
    transaction = service.process_transaction(
        db=test_db,
        account_id=4,
        account_number="ACC004",
        amount=Decimal("9999.99"),
        transaction_type="deposit",
    )
    
    assert transaction.fraud_detected is False


def test_get_transactions_all(test_db):
    """Test getting all transactions"""
    # Create multiple transactions
    service.process_transaction(test_db, 1, "ACC001", Decimal("100.00"), "deposit")
    service.process_transaction(test_db, 2, "ACC002", Decimal("200.00"), "deposit")
    service.process_transaction(test_db, 1, "ACC001", Decimal("50.00"), "withdraw")
    
    transactions = service.get_transactions(test_db)
    assert len(transactions) == 3


def test_get_transactions_by_account_id(test_db):
    """Test filtering transactions by account ID"""
    service.process_transaction(test_db, 1, "ACC001", Decimal("100.00"), "deposit")
    service.process_transaction(test_db, 2, "ACC002", Decimal("200.00"), "deposit")
    service.process_transaction(test_db, 1, "ACC001", Decimal("50.00"), "withdraw")
    
    transactions = service.get_transactions(test_db, account_id=1)
    assert len(transactions) == 2
    assert all(t.account_id == 1 for t in transactions)


def test_get_transactions_pagination(test_db):
    """Test transaction pagination"""
    # Create 5 transactions
    for i in range(5):
        service.process_transaction(
            test_db, i + 1, f"ACC{i+1:03d}", Decimal("100.00"), "deposit"
        )
    
    transactions = service.get_transactions(test_db, skip=2, limit=2)
    assert len(transactions) == 2


def test_get_transactions_empty(test_db):
    """Test getting transactions when none exist"""
    transactions = service.get_transactions(test_db)
    assert len(transactions) == 0


def test_transaction_ordering(test_db):
    """Test that transactions are ordered by processed_at descending"""
    service.process_transaction(test_db, 1, "ACC001", Decimal("100.00"), "deposit")
    service.process_transaction(test_db, 1, "ACC001", Decimal("200.00"), "deposit")
    
    transactions = service.get_transactions(test_db, account_id=1)
    assert len(transactions) == 2
    # Most recent should be first
    assert transactions[0].amount == Decimal("200.00")
    assert transactions[1].amount == Decimal("100.00")

