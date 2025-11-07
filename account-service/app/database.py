import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Add parent directory to path to import shared module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.logging_config import get_logger  # pylint: disable=wrong-import-position

logger = get_logger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

Base = declarative_base()

# Lazy initialization - only create engine if DATABASE_URL is set
engine = None
SessionLocal = None

if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for getting database session"""
    if SessionLocal is None:
        logger.error(
            "database_connection_failed",
            reason="DATABASE_URL_environment_variable_not_set",
            error="DATABASE_URL environment variable is not set",
        )
        raise RuntimeError("DATABASE_URL environment variable is not set")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
