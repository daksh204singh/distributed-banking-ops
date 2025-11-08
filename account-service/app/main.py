import time
import uuid

import structlog
from fastapi import FastAPI, Request

from app.database import Base, engine
from app.router import router
from shared.logging_config import configure_logging, get_logger

# Configure structured logging
configure_logging(service_name="account-service")
logger = get_logger(__name__)

# Create database tables (only if engine is initialized)
if engine is not None:
    Base.metadata.create_all(bind=engine)
    logger.info("database_tables_initialized")

app = FastAPI(title="Account Service", description="Microservice for managing bank accounts", version="1.0.0")


# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests and responses with correlation ID."""
    # Generate or extract correlation ID
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

    logger.info(
        "request_started",
        method=request.method,
        path=request.url.path,
        query_params=str(request.query_params) if request.query_params else None,
        client_ip=request.client.host if request.client else None,
    )

    start_time = time.time()
    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            process_time_ms=round(process_time * 1000, 2),
        )

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            "request_failed",
            method=request.method,
            path=request.url.path,
            error=str(e),
            error_type=type(e).__name__,
            process_time_ms=round(process_time * 1000, 2),
            exc_info=True,
        )
        raise


app.include_router(router)


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "account-service"}


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "service": "account-service",
        "version": "1.0.0",
        "endpoints": {
            "POST /accounts": "Create new account",
            "GET /accounts/{id}": "Get account balance",
            "PUT /accounts/{id}/deposit": "Deposit funds",
            "PUT /accounts/{id}/withdraw": "Withdraw funds",
        },
    }
