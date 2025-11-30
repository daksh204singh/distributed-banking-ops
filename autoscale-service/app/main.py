"""Minimal auto-scaling webhook service."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from app.router import router

app = FastAPI(title="Auto-Scaling Service", version="1.0.0")
app.include_router(router)

# Add Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app)


@app.get("/health")
def health():
    return {"status": "healthy"}
