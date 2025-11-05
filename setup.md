# Distributed Banking Operations - Setup Guide

This project implements a microservices banking system with two services: Account Service and Transaction Service, connected via RabbitMQ message queue.

## Architecture

- **Account Service** (Port 8000): Handles account creation, balance lookups, deposits, and withdrawals
- **Transaction Service** (Port 8001): Processes transaction events asynchronously and maintains audit trail
- **PostgreSQL**: Shared database for both services
- **RabbitMQ**: Message queue for event-driven communication

## Prerequisites

- Docker and Docker Compose installed
- At least 4GB of available RAM
- Ports 5432, 5672, 8000, 8001, and 15672 available

## Quick Start

1. **Clone the repository** (if not already done):
   ```bash
   cd distributed-banking-ops
   ```

2. **Start all services using Docker Compose**:
   ```bash
   docker-compose up --build
   ```

   This will:
   - Build Docker images for both services
   - Start PostgreSQL database
   - Start RabbitMQ broker
   - Start Account Service on port 8000
   - Start Transaction Service on port 8001

3. **Verify services are running**:
   ```bash
   # Check Account Service
   curl http://localhost:8000/health
   
   # Check Transaction Service
   curl http://localhost:8001/health
   ```

## API Endpoints

### Account Service (http://localhost:8000)

#### Create Account
```bash
curl -X POST "http://localhost:8000/accounts" \
  -H "Content-Type: application/json" \
  -d '{"account_number": "ACC123456"}'
```

#### Get Account Balance
```bash
curl "http://localhost:8000/accounts/1"
```

#### Deposit Funds
```bash
curl -X PUT "http://localhost:8000/accounts/1/deposit" \
  -H "Content-Type: application/json" \
  -d '{"amount": 1000.00}'
```

#### Withdraw Funds
```bash
curl -X PUT "http://localhost:8000/accounts/1/withdraw" \
  -H "Content-Type: application/json" \
  -d '{"amount": 500.00}'
```

### Transaction Service (http://localhost:8001)

#### Get Transaction History
```bash
# Get all transactions
curl "http://localhost:8001/transactions"

# Get transactions for specific account
curl "http://localhost:8001/transactions?account_id=1"

# With pagination
curl "http://localhost:8001/transactions?skip=0&limit=10"
```

## Example Workflow

1. **Create an account**:
   ```bash
   curl -X POST "http://localhost:8000/accounts" \
     -H "Content-Type: application/json" \
     -d '{"account_number": "ACC001"}'
   ```
   Response will include the account `id` (e.g., `1`)

2. **Deposit funds**:
   ```bash
   curl -X PUT "http://localhost:8000/accounts/1/deposit" \
     -H "Content-Type: application/json" \
     -d '{"amount": 5000.00}'
   ```
   This will:
   - Update the account balance
   - Publish a `transaction.created` event to RabbitMQ
   - Transaction Service will automatically process and store the transaction

3. **Check transaction history**:
   ```bash
   curl "http://localhost:8001/transactions?account_id=1"
   ```

4. **Withdraw funds**:
   ```bash
   curl -X PUT "http://localhost:8000/accounts/1/withdraw" \
     -H "Content-Type: application/json" \
     -d '{"amount": 2000.00}'
   ```

## Monitoring

### RabbitMQ Management UI

Access the RabbitMQ Management UI at: http://localhost:15672

- Username: `guest`
- Password: `guest`

You can monitor queues, messages, and connections here.

### API Documentation

- Account Service Swagger UI: http://localhost:8000/docs
- Transaction Service Swagger UI: http://localhost:8001/docs

### Database Access

To access the PostgreSQL database directly:

```bash
docker exec -it banking-postgres psql -U bankuser -d banking_db
```

Then you can query:
```sql
-- View accounts
SELECT * FROM accounts;

-- View transactions
SELECT * FROM transactions;

-- View transactions with fraud detection
SELECT * FROM transactions WHERE fraud_detected = true;
```

## Environment Variables

Both services support environment variables (see `.env.example` files):

- `DATABASE_URL`: PostgreSQL connection string
- `RABBITMQ_HOST`: RabbitMQ hostname
- `RABBITMQ_PORT`: RabbitMQ port
- `RABBITMQ_USER`: RabbitMQ username
- `RABBITMQ_PASSWORD`: RabbitMQ password
- `RABBITMQ_QUEUE`: Queue name for transaction events

## Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clears database and RabbitMQ data)
docker-compose down -v
```

## Development

### Running Services Locally (without Docker)

1. **Start PostgreSQL and RabbitMQ** (using Docker Compose):
   ```bash
   docker-compose up postgres rabbitmq
   ```

2. **Set up virtual environment**:
   ```bash
   # For Account Service
   cd account-service
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run Account Service**:
   ```bash
   cd account-service
   uvicorn app.main:app --reload --port 8000
   ```

4. **Run Transaction Service** (in another terminal):
   ```bash
   cd transaction-service
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8001
   ```

## Troubleshooting

### Services not starting

- Check if ports are already in use:
  ```bash
  lsof -i :8000
  lsof -i :8001
  lsof -i :5432
  ```

### Database connection errors

- Ensure PostgreSQL container is healthy:
  ```bash
  docker-compose ps
  ```
- Wait for health checks to pass before making requests

### RabbitMQ connection errors

- Check RabbitMQ logs:
  ```bash
  docker-compose logs rabbitmq
  ```
- Verify RabbitMQ is accessible:
  ```bash
  curl http://localhost:15672/api/overview
  ```

### Transaction events not processing

- Check Transaction Service logs:
  ```bash
  docker-compose logs transaction-service
  ```
- Verify RabbitMQ queue has messages in Management UI

## Project Structure

```
distributed-banking-ops/
├── docker-compose.yml          # Orchestration file
├── setup.md                    # This file
├── account-service/            # Account microservice
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   └── app/
│       ├── main.py            # FastAPI app
│       ├── models.py          # Database models
│       ├── schemas.py         # Pydantic schemas
│       ├── router.py          # API routes
│       ├── service.py         # Business logic
│       └── publisher.py       # RabbitMQ publisher
├── transaction-service/        # Transaction microservice
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   └── app/
│       ├── main.py            # FastAPI app
│       ├── models.py          # Database models
│       ├── schemas.py         # Pydantic schemas
│       ├── router.py          # API routes
│       ├── service.py         # Transaction processing
│       └── consumer.py        # RabbitMQ consumer
└── shared/                     # Shared utilities
    └── events.py              # Event schemas
```

