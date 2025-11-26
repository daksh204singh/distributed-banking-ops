"""
Load testing for distributed banking operations using Locust.

This file defines user behavior patterns to simulate realistic banking operations:
- Account creation
- Balance checks
- Deposits
- Withdrawals
- Transaction history queries

Run with: locust -f locustfile.py --host=http://localhost:8000
"""

import random
import time
import threading
from decimal import Decimal
from locust import HttpUser, task, between, events

# Shared list to track account IDs created by BankingUser instances
# This allows TransactionServiceUser to query only existing accounts
_known_account_ids = []
_account_ids_lock = threading.Lock()


class BankingUser(HttpUser):
    """
    Simulates a banking user performing various operations.
    
    User behavior:
    1. Creates an account
    2. Checks balance
    3. Performs deposits
    4. Performs withdrawals
    5. Queries transaction history
    """
    
    # Account service runs on port 8000
    host = "http://localhost:8000"
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    account_id = None
    account_number = None
    
    def on_start(self):
        """Called when a simulated user starts. Creates an account."""
        # Create a unique account for this user
        self.account_number = f"LOAD_TEST_{int(time.time())}_{random.randint(1000, 9999)}"
        response = self.client.post(
            "/accounts",
            json={"account_number": self.account_number},
            name="Create Account"
        )
        if response.status_code == 201:
            data = response.json()
            self.account_id = data["id"]
            # Add account ID to shared list for TransactionServiceUser
            with _account_ids_lock:
                _known_account_ids.append(self.account_id)
            # Initial deposit to have funds available
            self.client.put(
                f"/accounts/{self.account_id}/deposit",
                json={"amount": "1000.00"},
                name="Initial Deposit"
            )
    
    @task(3)
    def check_balance(self):
        """Check account balance - most common operation."""
        if self.account_id:
            self.client.get(
                f"/accounts/{self.account_id}",
                name="Get Account Balance"
            )
    
    @task(2)
    def deposit_funds(self):
        """Deposit funds - common operation."""
        if self.account_id:
            amount = round(random.uniform(10.00, 500.00), 2)
            self.client.put(
                f"/accounts/{self.account_id}/deposit",
                json={"amount": str(amount)},
                name="Deposit Funds"
            )
    
    @task(1)
    def withdraw_funds(self):
        """Withdraw funds - common operation. Ensures withdrawal is within account balance."""
        if self.account_id:
            # First, get the current account balance
            balance_response = self.client.get(
                f"/accounts/{self.account_id}",
                name="Get Account Balance (for withdrawal check)"
            )
            
            if balance_response.status_code == 200:
                account_data = balance_response.json()
                current_balance = Decimal(str(account_data["balance"]))
                
                # Only withdraw if balance is sufficient (at least $10)
                if current_balance >= Decimal("10.00"):
                    # Calculate maximum withdrawal: up to 90% of balance, capped at $200
                    # This ensures we don't drain the account completely
                    max_withdrawal_pct = current_balance * Decimal("0.9")
                    max_withdrawal = min(max_withdrawal_pct, Decimal("200.00"))
                    
                    # Ensure max withdrawal doesn't exceed actual balance
                    max_withdrawal = min(max_withdrawal, current_balance)
                    
                    min_withdrawal = Decimal("10.00")
                    
                    # Only proceed if we can withdraw at least the minimum
                    if max_withdrawal >= min_withdrawal:
                        # Generate random amount between min and max
                        amount = round(
                            random.uniform(
                                float(min_withdrawal),
                                float(max_withdrawal)
                            ),
                            2
                        )
                        
                        self.client.put(
                            f"/accounts/{self.account_id}/withdraw",
                            json={"amount": str(amount)},
                            name="Withdraw Funds"
                        )


class TransactionServiceUser(HttpUser):
    """
    Simulates queries to the transaction service.
    
    This user type focuses on read-heavy operations:
    - Querying transaction history
    - Filtering by account ID
    - Pagination
    """
    
    # Transaction service runs on port 8001
    host = "http://localhost:8001"
    wait_time = between(0.5, 2)
    
    @task(5)
    def get_all_transactions(self):
        """Get all transactions with pagination."""
        skip = random.randint(0, 100)
        limit = random.choice([10, 25, 50, 100])
        self.client.get(
            f"/transactions?skip={skip}&limit={limit}",
            name="Get All Transactions"
        )
    
    @task(2)
    def get_transactions_by_account(self):
        """Get transactions for a specific account that exists."""
        # Get account ID from the shared list of known accounts
        with _account_ids_lock:
            if _known_account_ids:
                # Select a random account from known accounts
                account_id = random.choice(_known_account_ids)
            else:
                # If no accounts exist yet, skip this task
                return
        
        # Query transactions for this account
        self.client.get(
            f"/transactions?account_id={account_id}",
            name="Get Transactions By Account"
        )
    
    @task(1)
    def health_check(self):
        """Health check endpoint."""
        self.client.get("/health", name="Transaction Service Health")


# Event hooks for custom metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when the test starts."""
    print("🚀 Load test started")
    print(f"   Target host: {environment.host}")
    print(f"   Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when the test stops."""
    print("✅ Load test completed")
    stats = environment.stats
    print(f"   Total requests: {stats.total.num_requests}")
    print(f"   Total failures: {stats.total.num_failures}")
    if stats.total.num_requests > 0:
        failure_rate = (stats.total.num_failures / stats.total.num_requests) * 100
        print(f"   Failure rate: {failure_rate:.2f}%")
        print(f"   Average response time: {stats.total.avg_response_time:.2f}ms")

