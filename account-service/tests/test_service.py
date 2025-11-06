import pytest
from decimal import Decimal

from app import service
from app.models import Account


def test_create_account(test_db):
    """Test creating a new account"""
    account = service.create_account(test_db, "ACC001")
    assert account.account_number == "ACC001"
    assert account.balance == Decimal("0.00")
    assert account.id is not None


def test_get_account(test_db):
    """Test getting an account by ID"""
    account = service.create_account(test_db, "ACC002")
    retrieved = service.get_account(test_db, account.id)
    assert retrieved is not None
    assert retrieved.account_number == "ACC002"
    assert retrieved.id == account.id


def test_get_account_by_number(test_db):
    """Test getting an account by account number"""
    account = service.create_account(test_db, "ACC003")
    retrieved = service.get_account_by_number(test_db, "ACC003")
    assert retrieved is not None
    assert retrieved.id == account.id


def test_get_account_not_found(test_db):
    """Test getting a non-existent account"""
    account = service.get_account(test_db, 999)
    assert account is None


def test_deposit(test_db, mock_publisher):
    """Test depositing funds to an account"""
    account = service.create_account(test_db, "ACC004")
    updated = service.deposit(test_db, account.id, Decimal("100.50"))
    
    assert updated.balance == Decimal("100.50")
    assert len(mock_publisher) == 1
    assert mock_publisher[0]["transaction_type"] == "deposit"
    assert mock_publisher[0]["amount"] == Decimal("100.50")


def test_deposit_multiple(test_db, mock_publisher):
    """Test multiple deposits"""
    account = service.create_account(test_db, "ACC005")
    service.deposit(test_db, account.id, Decimal("50.00"))
    service.deposit(test_db, account.id, Decimal("25.50"))
    
    updated = service.get_account(test_db, account.id)
    assert updated.balance == Decimal("75.50")
    assert len(mock_publisher) == 2


def test_deposit_account_not_found(test_db):
    """Test depositing to non-existent account"""
    result = service.deposit(test_db, 999, Decimal("100.00"))
    assert result is None


def test_withdraw(test_db, mock_publisher):
    """Test withdrawing funds from an account"""
    account = service.create_account(test_db, "ACC006")
    service.deposit(test_db, account.id, Decimal("100.00"))
    
    updated = service.withdraw(test_db, account.id, Decimal("30.00"))
    assert updated.balance == Decimal("70.00")
    assert len(mock_publisher) == 2
    assert mock_publisher[1]["transaction_type"] == "withdraw"


def test_withdraw_insufficient_funds(test_db):
    """Test withdrawing more than available balance"""
    account = service.create_account(test_db, "ACC007")
    service.deposit(test_db, account.id, Decimal("50.00"))
    
    with pytest.raises(ValueError, match="Insufficient funds"):
        service.withdraw(test_db, account.id, Decimal("100.00"))


def test_withdraw_account_not_found(test_db):
    """Test withdrawing from non-existent account"""
    result = service.withdraw(test_db, 999, Decimal("50.00"))
    assert result is None


def test_withdraw_exact_balance(test_db, mock_publisher):
    """Test withdrawing the exact balance"""
    account = service.create_account(test_db, "ACC008")
    service.deposit(test_db, account.id, Decimal("100.00"))
    
    updated = service.withdraw(test_db, account.id, Decimal("100.00"))
    assert updated.balance == Decimal("0.00")

