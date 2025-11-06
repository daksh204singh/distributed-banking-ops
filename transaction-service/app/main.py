import logging
import threading

from fastapi import FastAPI

from app.consumer import start_consumer
from app.database import Base, engine
from app.router import router

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Create database tables (only if engine is initialized)
if engine is not None:
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Transaction Service", description="Microservice for processing and auditing transactions", version="1.0.0"
)

app.include_router(router)

# Start RabbitMQ consumer in background thread


@app.on_event("startup")
def startup_event():
    """Start RabbitMQ consumer on application startup"""
    consumer_thread = threading.Thread(target=start_consumer, daemon=True)
    consumer_thread.start()
    logging.info("Transaction service started and consumer thread initialized")


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "transaction-service"}


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "service": "transaction-service",
        "version": "1.0.0",
        "endpoints": {
            "GET /transactions": "Get transaction history",
            "GET /transactions?account_id={id}": "Get transactions for specific account",
        },
    }
