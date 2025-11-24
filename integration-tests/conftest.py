"""Pytest configuration and fixtures for integration tests."""

import os
import sys
from pathlib import Path
import pytest
import httpx
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from testcontainers.compose import DockerCompose

# Add integration-tests directory to path for imports
integration_tests_dir = Path(__file__).parent
if str(integration_tests_dir) not in sys.path:
    sys.path.insert(0, str(integration_tests_dir))

# Get project root (parent of integration-tests directory)
PROJECT_ROOT = integration_tests_dir.parent


@pytest.fixture(scope="session")
def docker_compose_services():
    """
    Start all services using DockerCompose from testcontainers.
    
    This fixture starts the entire docker-compose setup and manages
    the lifecycle of all containers. Uses DockerCompose's built-in
    wait functionality to wait for services to be ready.
    """
    # Path to docker-compose.yml relative to project root
    compose_file = PROJECT_ROOT / "docker-compose.yml"
    
    print("\n🚀 Starting Docker Compose services...")
    print(f"   Context: {PROJECT_ROOT}")
    print(f"   Compose file: {compose_file.name}")
    
    # Initialize DockerCompose with wait enabled
    # DockerCompose will wait for services defined in docker-compose.yml
    compose = DockerCompose(
        context=str(PROJECT_ROOT),
        compose_file_name=str(compose_file.name),
        pull=False,
        build=True,
        wait=True,
    )
    
    try:
        print("   Building and starting containers...")
        # Start services - DockerCompose will wait for health checks
        compose.start()
        print("   ✅ All services started and healthy\n")
        
        yield compose
    finally:
        print("\n🛑 Stopping Docker Compose services...")
        compose.stop()
        print("✅ Services stopped\n")


@pytest.fixture(scope="session")
def account_service_url(docker_compose_services):
    """Base URL for account service from docker-compose container."""
    host = docker_compose_services.get_service_host("account-service", port=8000)
    port = docker_compose_services.get_service_port("account-service", port=8000)
    return f"http://{host}:{port}"


@pytest.fixture(scope="session")
def transaction_service_url(docker_compose_services):
    """Base URL for transaction service from docker-compose container."""
    host = docker_compose_services.get_service_host("transaction-service", port=8001)
    port = docker_compose_services.get_service_port("transaction-service", port=8001)
    return f"http://{host}:{port}"


@pytest.fixture(scope="session")
def database_url(docker_compose_services):
    """
    Database connection URL from docker-compose container.
    
    Constructs the URL using the postgres service host/port from docker-compose
    and environment variables for credentials.
    """
    # Get host and port from docker-compose service
    host = docker_compose_services.get_service_host("banking-postgres", port=5432)
    port = docker_compose_services.get_service_port("banking-postgres", port=5432)
    
    # Get credentials from environment variables
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    database = os.getenv("POSTGRES_DB")
    
    # Construct PostgreSQL connection URL
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


@pytest.fixture(scope="session")
def account_service_client(account_service_url, docker_compose_services):
    """HTTP client for account service."""
    with httpx.Client(base_url=account_service_url, timeout=30.0) as client:
        yield client


@pytest.fixture(scope="session")
def transaction_service_client(transaction_service_url, docker_compose_services):
    """HTTP client for transaction service."""
    with httpx.Client(base_url=transaction_service_url, timeout=30.0) as client:
        yield client


@pytest.fixture(scope="function")
def test_db_session(database_url):
    """
    Create a database session for verification queries.
    
    This connects to the database from docker-compose services
    to verify state after operations.
    """
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture(scope="function", autouse=True)
def cleanup_test_data(test_db_session):
    """
    Clean up test data between tests.
    
    This fixture runs automatically after each test to ensure clean state.
    """
    # Clean up accounts and transactions created during tests
    # We identify test data by account numbers starting with "TEST_"
    yield
    try:
        # Delete transactions first (foreign key constraint)
        test_db_session.execute(
            text("DELETE FROM transactions WHERE account_number LIKE 'TEST_%'")
        )
        # Delete accounts
        test_db_session.execute(text("DELETE FROM accounts WHERE account_number LIKE 'TEST_%'"))
        test_db_session.commit()
    except Exception:
        test_db_session.rollback()
        # Don't fail tests if cleanup fails
