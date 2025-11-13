import time

from prometheus_client import Counter, Histogram, Gauge
from sqlalchemy import event
from sqlalchemy.engine import Engine

# Prometheus metrics for SQLAlchemy
QUERY_COUNT = Counter(
    "sqlalchemy_query_total",
    "Total number of executed SQL queries",
    ["method"],
)

QUERY_DURATION = Histogram(
    "sqlalchemy_query_duration_seconds",
    "SQL query duration in seconds",
    ["method"],
)

CONNECTIONS_IN_USE = Gauge(
    "sqlalchemy_connections_in_use",
    "Number of connections currently checked out",
)


def setup_db_metrics(engine: Engine) -> None:
    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):  # pylint: disable=unused-argument
        conn.info["query_start_time"] = time.time()

    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):  # pylint: disable=unused-argument
        duration = time.time() - conn.info.pop("query_start_time", time.time())
        method = statement.split()[0] if statement else "UNKNOWN"
        QUERY_DURATION.labels(method=method).observe(duration)
        QUERY_COUNT.labels(method=method).inc()

    @event.listens_for(engine, "connect")
    def connect(dbapi_connection, connection_record):  # pylint: disable=unused-argument
        CONNECTIONS_IN_USE.inc()

    @event.listens_for(engine, "close")
    def close(dbapi_connection, connection_record):  # pylint: disable=unused-argument
        CONNECTIONS_IN_USE.dec()


