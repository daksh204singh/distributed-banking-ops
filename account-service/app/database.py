import os
from shared.logging_config import get_logger
from shared.prometheus.db_metrics import setup_db_metrics
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logger = get_logger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

Base = declarative_base()

# Lazy initialization - only create engine if DATABASE_URL is set
engine = None
SessionLocal = None

if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
    setup_db_metrics(engine)
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
