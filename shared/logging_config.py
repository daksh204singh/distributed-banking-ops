"""Structured logging configuration for microservices."""

import logging
import os
import sys

import structlog
from structlog.stdlib import LoggerFactory


def configure_logging(service_name: str, log_level: str = None) -> None:
    """
    Configure structured logging for a microservice.

    Args:
        service_name: Name of the service (e.g., 'account-service')
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                   If None, reads from LOG_LEVEL environment variable or defaults to INFO.
    """
    # Get log level from parameter, environment variable, or default to INFO
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,  # Merge context variables
            structlog.stdlib.filter_by_level,  # Filter by log level
            structlog.stdlib.add_logger_name,  # Add logger name
            structlog.stdlib.add_log_level,  # Add log level
            structlog.stdlib.PositionalArgumentsFormatter(),  # Format positional args
            structlog.processors.TimeStamper(fmt="iso"),  # ISO 8601 timestamps
            structlog.processors.StackInfoRenderer(),  # Stack info for exceptions
            structlog.processors.format_exc_info,  # Format exceptions
            structlog.processors.UnicodeDecoder(),  # Decode unicode
            structlog.processors.JSONRenderer(),  # JSON output
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Add service name to all logs via context
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(service=service_name)


def get_logger(name: str = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


# Masking functions for sensitive data
def mask_account_number(account_number: str) -> str:
    """
    Mask account number showing first 3 and last 3 characters.

    Args:
        account_number: The account number to mask

    Returns:
        Masked account number (e.g., "ACC123456" -> "ACC****456")
    """
    if not account_number or len(account_number) < 6:
        return "****"
    return f"{account_number[:3]}****{account_number[-3:]}"


def mask_balance(balance: str) -> str:
    """
    Mask balance showing first digit and last 2 characters.

    Args:
        balance: The balance to mask (as string)

    Returns:
        Masked balance (e.g., "1000.50" -> "1***50")
    """
    if not balance or len(balance) < 3:
        return "***"
    return f"{balance[0]}****{balance[-2:]}"


def mask_amount(amount: str) -> str:
    """
    Mask transaction amount showing first digit and last 2 characters.

    Args:
        amount: The amount to mask (as string)

    Returns:
        Masked amount (e.g., "500.00" -> "5***00")
    """
    if not amount or len(amount) < 3:
        return "***"
    return f"{amount[0]}****{amount[-2:]}"
