from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import TransactionResponse
from app.service import get_transactions

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=List[TransactionResponse])
def list_transactions(
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get transaction history"""
    transactions = get_transactions(db, account_id=account_id, skip=skip, limit=limit)
    return transactions


@router.get("/test/error-500")
def trigger_500_error():
    """Test endpoint to trigger 500 errors for monitoring/testing"""
    raise Exception("Intentional 500 error for testing error monitoring and metrics")
