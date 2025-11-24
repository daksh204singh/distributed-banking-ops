"""Prometheus shared helpers."""

# Import db_metrics only if sqlalchemy is available (for services that use databases)
try:
    from .db_metrics import setup_db_metrics  # noqa: F401
except ImportError:
    pass  # sqlalchemy not available, skip db_metrics

from .error_metrics import register_error_metrics  # noqa: F401
from .rabbit_metrics import (  # noqa: F401
    record_consume,
    record_publish,
    register_rabbitmq_metrics,
)
