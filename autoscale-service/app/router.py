"""Auto-scaling webhook endpoint."""
from fastapi import APIRouter, HTTPException
from app.schemas import WebhookPayload
from app.service import process_webhook_alerts

router = APIRouter()


@router.post("/webhook/autoscale")
async def autoscale_webhook(payload: WebhookPayload):
    """Receive Grafana alert webhook and trigger scaling.
    
    Args:
        payload: Webhook payload from Grafana containing alert information
    
    Returns:
        Dictionary with status and results
    
    Raises:
        HTTPException: If processing fails
    """
    try:
        result = process_webhook_alerts(payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process webhook: {str(e)}")
