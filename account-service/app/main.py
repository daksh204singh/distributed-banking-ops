from fastapi import FastAPI
from app.database import engine, Base
from app.router import router
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Account Service", description="Microservice for managing bank accounts", version="1.0.0")

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
