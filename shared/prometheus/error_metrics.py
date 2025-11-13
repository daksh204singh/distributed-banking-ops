from fastapi import FastAPI, Request
from prometheus_client import Counter

ERRORS_TOTAL = Counter(
    "app_errors_total",
    "Application errors",
    ["endpoint", "status_class", "status_code"],
)


def register_error_metrics(app: FastAPI) -> None:
    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        response = await call_next(request)

        if response.status_code >= 400:
            route = request.scope.get("route")
            endpoint = getattr(route, "path", None) or request.url.path
            ERRORS_TOTAL.labels(
                endpoint=endpoint,
                status_class=f"{response.status_code // 100}xx",
                status_code=str(response.status_code),
            ).inc()

        return response


