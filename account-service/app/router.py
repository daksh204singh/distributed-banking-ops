from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import service
from app.schemas import AccountCreate, AccountResponse, DepositRequest, WithdrawRequest

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(account_data: AccountCreate, db: Session = Depends(get_db)):
    """Create a new account"""
    # Check if account number already exists
    existing_account = service.get_account_by_number(db, account_data.account_number)
    if existing_account:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account number already exists")

    account = service.create_account(db, account_data.account_number)
    return account


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(account_id: int, db: Session = Depends(get_db)):
    """Get account balance by ID"""
    account = service.get_account(db, account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account


@router.put("/{account_id}/deposit", response_model=AccountResponse)
def deposit(account_id: int, deposit_data: DepositRequest, db: Session = Depends(get_db)):
    """Deposit funds to account"""
    account = service.deposit(db, account_id, deposit_data.amount)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account


@router.put("/{account_id}/withdraw", response_model=AccountResponse)
def withdraw(account_id: int, withdraw_data: WithdrawRequest, db: Session = Depends(get_db)):
    """Withdraw funds from account"""
    try:
        account = service.withdraw(db, account_id, withdraw_data.amount)
        if not account:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
        return account
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
