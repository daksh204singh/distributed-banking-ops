import pytest
from decimal import Decimal

from fastapi import status


def test_create_account_endpoint(client):
    """Test POST /accounts endpoint"""
    response = client.post("/accounts", json={"account_number": "ACC_TEST_001"})
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["account_number"] == "ACC_TEST_001"
    assert data["balance"] == "0.00"
    assert "id" in data


def test_create_duplicate_account(client):
    """Test creating account with duplicate account number"""
    client.post("/accounts", json={"account_number": "ACC_DUP_001"})
    response = client.post("/accounts", json={"account_number": "ACC_DUP_001"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in response.json()["detail"]


def test_get_account_endpoint(client):
    """Test GET /accounts/{id} endpoint"""
    create_response = client.post("/accounts", json={"account_number": "ACC_GET_001"})
    account_id = create_response.json()["id"]
    
    response = client.get(f"/accounts/{account_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["account_number"] == "ACC_GET_001"


def test_get_account_not_found(client):
    """Test getting non-existent account"""
    response = client.get("/accounts/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_deposit_endpoint(client, mock_publisher):
    """Test PUT /accounts/{id}/deposit endpoint"""
    create_response = client.post("/accounts", json={"account_number": "ACC_DEP_001"})
    account_id = create_response.json()["id"]
    
    response = client.put(f"/accounts/{account_id}/deposit", json={"amount": "150.75"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["balance"] == "150.75"
    assert len(mock_publisher) == 1


def test_deposit_invalid_amount(client):
    """Test deposit with invalid amount"""
    create_response = client.post("/accounts", json={"account_number": "ACC_DEP_002"})
    account_id = create_response.json()["id"]
    
    response = client.put(f"/accounts/{account_id}/deposit", json={"amount": "-10.00"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_deposit_account_not_found(client):
    """Test deposit to non-existent account"""
    response = client.put("/accounts/99999/deposit", json={"amount": "100.00"})
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_withdraw_endpoint(client, mock_publisher):
    """Test PUT /accounts/{id}/withdraw endpoint"""
    create_response = client.post("/accounts", json={"account_number": "ACC_WD_001"})
    account_id = create_response.json()["id"]
    
    client.put(f"/accounts/{account_id}/deposit", json={"amount": "200.00"})
    response = client.put(f"/accounts/{account_id}/withdraw", json={"amount": "75.50"})
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["balance"] == "124.50"
    assert len(mock_publisher) == 2


def test_withdraw_insufficient_funds(client):
    """Test withdraw with insufficient funds"""
    create_response = client.post("/accounts", json={"account_number": "ACC_WD_002"})
    account_id = create_response.json()["id"]
    
    response = client.put(f"/accounts/{account_id}/withdraw", json={"amount": "100.00"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Insufficient funds" in response.json()["detail"]


def test_withdraw_account_not_found(client):
    """Test withdraw from non-existent account"""
    response = client.put("/accounts/99999/withdraw", json={"amount": "50.00"})
    assert response.status_code == status.HTTP_404_NOT_FOUND

