import pytest
from decimal import Decimal

from app import service
from fastapi import status


def test_get_transactions_endpoint(client, test_db):
    """Test GET /transactions endpoint"""
    # Create some transactions
    service.process_transaction(test_db, 1, "ACC001", Decimal("100.00"), "deposit")
    
    response = client.get("/transactions")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


def test_get_transactions_with_account_id(client, test_db):
    """Test GET /transactions?account_id={id} endpoint"""
    # Create transactions for different accounts
    service.process_transaction(test_db, 1, "ACC001", Decimal("100.00"), "deposit")
    service.process_transaction(test_db, 2, "ACC002", Decimal("200.00"), "deposit")
    service.process_transaction(test_db, 1, "ACC001", Decimal("50.00"), "withdraw")
    
    response = client.get("/transactions?account_id=1")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert all(t["account_id"] == 1 for t in data)


def test_get_transactions_pagination(client, test_db):
    """Test GET /transactions with pagination"""
    # Create 5 transactions
    for i in range(5):
        service.process_transaction(
            test_db, i + 1, f"ACC{i+1:03d}", Decimal("100.00"), "deposit"
        )
    
    response = client.get("/transactions?skip=2&limit=2")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2


def test_get_transactions_empty(client):
    """Test GET /transactions when no transactions exist"""
    response = client.get("/transactions")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

