"""Integration tests for account to transaction service flow."""

import time
from decimal import Decimal
from sqlalchemy import text
import pytest


class TestAccountToTransactionFlow:
    """Test end-to-end flow from account service to transaction service."""

    def test_create_account_and_deposit_creates_transaction(
        self,
        account_service_client,
        transaction_service_client,
        test_db_session,
    ):
        """Test that depositing to an account creates a transaction record."""
        # Create account
        account_number = f"TEST_{int(time.time())}"
        create_response = account_service_client.post(
            "/accounts", json={"account_number": account_number}
        )
        assert create_response.status_code == 201
        account_data = create_response.json()
        account_id = account_data["id"]
        assert account_data["balance"] == "0.00"

        # Deposit funds
        deposit_amount = "150.75"
        deposit_response = account_service_client.put(
            f"/accounts/{account_id}/deposit", json={"amount": deposit_amount}
        )
        assert deposit_response.status_code == 200
        assert deposit_response.json()["balance"] == deposit_amount

        # Wait for transaction to be processed (async message consumption)
        # Poll transaction service until transaction appears
        max_wait = 10.0
        start_time = time.time()
        transaction_found = False

        while time.time() - start_time < max_wait:
            transactions_response = transaction_service_client.get(
                f"/transactions?account_id={account_id}"
            )
            assert transactions_response.status_code == 200
            transactions = transactions_response.json()

            if transactions and len(transactions) > 0:
                # Verify transaction details
                transaction = transactions[0]
                assert transaction["account_id"] == account_id
                assert transaction["account_number"] == account_number
                assert transaction["amount"] == deposit_amount
                assert transaction["transaction_type"] == "deposit"
                transaction_found = True
                break

            time.sleep(0.5)

        assert transaction_found, "Transaction was not created within timeout period"

        # Verify in database directly
        result = test_db_session.execute(
            text(
                "SELECT * FROM transactions WHERE account_id = :account_id AND transaction_type = 'deposit'"
            ),
            {"account_id": account_id},
        )
        db_transaction = result.fetchone()
        assert db_transaction is not None
        assert str(db_transaction.amount) == deposit_amount

    def test_withdrawal_creates_transaction(
        self,
        account_service_client,
        transaction_service_client,
        test_db_session,
    ):
        """Test that withdrawing from an account creates a transaction record."""
        # Create account
        account_number = f"TEST_{int(time.time())}"
        create_response = account_service_client.post(
            "/accounts", json={"account_number": account_number}
        )
        assert create_response.status_code == 201
        account_id = create_response.json()["id"]

        # Deposit first
        deposit_response = account_service_client.put(
            f"/accounts/{account_id}/deposit", json={"amount": "200.00"}
        )
        assert deposit_response.status_code == 200

        # Wait for deposit transaction
        time.sleep(2)

        # Withdraw funds
        withdraw_amount = "75.50"
        withdraw_response = account_service_client.put(
            f"/accounts/{account_id}/withdraw", json={"amount": withdraw_amount}
        )
        assert withdraw_response.status_code == 200
        assert withdraw_response.json()["balance"] == "124.50"

        # Wait for withdrawal transaction to be processed
        max_wait = 10.0
        start_time = time.time()
        withdrawal_found = False

        while time.time() - start_time < max_wait:
            transactions_response = transaction_service_client.get(
                f"/transactions?account_id={account_id}"
            )
            assert transactions_response.status_code == 200
            transactions = transactions_response.json()

            # Should have both deposit and withdrawal
            if len(transactions) >= 2:
                withdrawal_transactions = [
                    t for t in transactions if t["transaction_type"] == "withdraw"
                ]
                if withdrawal_transactions:
                    withdrawal = withdrawal_transactions[0]
                    assert withdrawal["account_id"] == account_id
                    assert withdrawal["amount"] == withdraw_amount
                    withdrawal_found = True
                    break

            time.sleep(0.5)

        assert withdrawal_found, "Withdrawal transaction was not created within timeout period"

    def test_multiple_transactions_are_ordered_correctly(
        self,
        account_service_client,
        transaction_service_client,
    ):
        """Test that multiple transactions are recorded in correct order."""
        # Create account
        account_number = f"TEST_{int(time.time())}"
        create_response = account_service_client.post(
            "/accounts", json={"account_number": account_number}
        )
        assert create_response.status_code == 201
        account_id = create_response.json()["id"]

        # Perform multiple operations
        account_service_client.put(f"/accounts/{account_id}/deposit", json={"amount": "100.00"})
        time.sleep(1)
        account_service_client.put(f"/accounts/{account_id}/deposit", json={"amount": "50.00"})
        time.sleep(1)
        account_service_client.put(f"/accounts/{account_id}/withdraw", json={"amount": "25.00"})

        # Wait for all transactions to be processed
        max_wait = 15.0
        start_time = time.time()
        all_transactions_found = False

        while time.time() - start_time < max_wait:
            transactions_response = transaction_service_client.get(
                f"/transactions?account_id={account_id}"
            )
            assert transactions_response.status_code == 200
            transactions = transactions_response.json()

            if len(transactions) >= 3:
                # Verify we have the expected transactions
                amounts = [Decimal(str(t["amount"])) for t in transactions]
                types = [t["transaction_type"] for t in transactions]

                assert Decimal("100.00") in amounts
                assert Decimal("50.00") in amounts
                assert Decimal("25.00") in amounts
                assert "deposit" in types
                assert "withdraw" in types
                all_transactions_found = True
                break

            time.sleep(0.5)

        assert all_transactions_found, "Not all transactions were created within timeout period"

    def test_transaction_appears_in_transaction_history(
        self,
        account_service_client,
        transaction_service_client,
    ):
        """Test that transactions appear in transaction service history."""
        # Create account
        account_number = f"TEST_{int(time.time())}"
        create_response = account_service_client.post(
            "/accounts", json={"account_number": account_number}
        )
        assert create_response.status_code == 201
        account_id = create_response.json()["id"]

        # Deposit
        account_service_client.put(f"/accounts/{account_id}/deposit", json={"amount": "99.99"})

        # Wait and verify transaction appears in history
        max_wait = 10.0
        start_time = time.time()

        while time.time() - start_time < max_wait:
            # Get all transactions
            all_transactions_response = transaction_service_client.get("/transactions")
            assert all_transactions_response.status_code == 200
            all_transactions = all_transactions_response.json()

            # Get filtered transactions
            filtered_response = transaction_service_client.get(
                f"/transactions?account_id={account_id}"
            )
            assert filtered_response.status_code == 200
            filtered_transactions = filtered_response.json()

            # Check if our transaction appears in both
            if filtered_transactions:
                transaction = filtered_transactions[0]
                assert transaction["account_id"] == account_id
                assert transaction["amount"] == "99.99"

                # Verify it's also in the full list
                matching = [t for t in all_transactions if t["id"] == transaction["id"]]
                assert len(matching) == 1
                break

            time.sleep(0.5)

    def test_insufficient_funds_does_not_create_transaction(
        self,
        account_service_client,
        transaction_service_client,
    ):
        """Test that failed withdrawal due to insufficient funds doesn't create transaction."""
        # Create account
        account_number = f"TEST_{int(time.time())}"
        create_response = account_service_client.post(
            "/accounts", json={"account_number": account_number}
        )
        assert create_response.status_code == 201
        account_id = create_response.json()["id"]

        # Try to withdraw without funds
        withdraw_response = account_service_client.put(
            f"/accounts/{account_id}/withdraw", json={"amount": "100.00"}
        )
        assert withdraw_response.status_code == 400
        assert "Insufficient funds" in withdraw_response.json()["detail"]

        # Wait a bit and verify no transaction was created
        time.sleep(3)
        transactions_response = transaction_service_client.get(
            f"/transactions?account_id={account_id}"
        )
        assert transactions_response.status_code == 200
        transactions = transactions_response.json()
        assert len(transactions) == 0

