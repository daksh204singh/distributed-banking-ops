"""Webhook payload schemas."""
from typing import Dict, Any, Optional
from pydantic import BaseModel


class AlertLabel(BaseModel):
    service: Optional[str] = ""
    alertname: Optional[str] = ""
    job: Optional[str] = ""


class Alert(BaseModel):
    status: str
    labels: AlertLabel
    annotations: Dict[str, Any] = {}


class WebhookPayload(BaseModel):
    alerts: list[Alert]
