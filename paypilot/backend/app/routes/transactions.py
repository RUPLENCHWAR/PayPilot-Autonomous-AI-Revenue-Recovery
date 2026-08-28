from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Customer, Transaction
from app.schemas import CustomerOut, TransactionOut
from app.services.recovery_service import opportunity_to_dict
from app.models import RecoveryOpportunity

router = APIRouter(tags=["transactions"])


def serialize_tx(tx: Transaction) -> TransactionOut:
    return TransactionOut(
        id=tx.id,
        external_transaction_id=tx.external_transaction_id,
        customer_id=tx.customer_id,
        amount=tx.amount,
        currency=tx.currency,
        status=tx.status,
        payment_method=tx.payment_method,
        failure_reason=tx.failure_reason,
        created_at=tx.created_at,
        recovered=tx.recovered,
        recovery_probability=tx.recovery_probability,
        recommended_action=tx.recommended_action,
        customer_name=tx.customer.name if tx.customer else None,
        customer_email=tx.customer.email if tx.customer else None,
    )


@router.get("/transactions")
def list_transactions(
    status: Optional[str] = None,
    recovered: Optional[bool] = None,
    q: Optional[str] = None,
    limit: int = Query(100, le=300),
    db: Session = Depends(get_db),
):
    query = db.query(Transaction).options(joinedload(Transaction.customer)).order_by(Transaction.created_at.desc())
    if status:
        query = query.filter(Transaction.status == status)
    if recovered is not None:
        query = query.filter(Transaction.recovered.is_(recovered))
    if q:
        like = f"%{q}%"
        query = query.join(Customer).filter(
            (Transaction.external_transaction_id.ilike(like))
            | (Customer.name.ilike(like))
            | (Customer.email.ilike(like))
        )
    rows = query.limit(limit).all()
    return {"items": [serialize_tx(t) for t in rows], "count": len(rows)}


@router.get("/transactions/{transaction_id}")
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    tx = (
        db.query(Transaction)
        .options(joinedload(Transaction.customer))
        .filter(Transaction.id == transaction_id)
        .first()
    )
    if not tx:
        raise HTTPException(404, "Transaction not found")
    history = (
        db.query(Transaction)
        .filter(Transaction.customer_id == tx.customer_id)
        .order_by(Transaction.created_at.desc())
        .all()
    )
    opps = (
        db.query(RecoveryOpportunity)
        .filter(RecoveryOpportunity.transaction_id == tx.id)
        .all()
    )
    return {
        "transaction": serialize_tx(tx),
        "customer": tx.customer,
        "history": [serialize_tx(h) for h in history],
        "opportunities": [opportunity_to_dict(o) for o in opps],
    }


@router.get("/customers")
def list_customers(db: Session = Depends(get_db)):
    rows = db.query(Customer).order_by(Customer.lifetime_value.desc()).all()
    return {"items": [CustomerOut.model_validate(c) for c in rows], "count": len(rows)}


@router.get("/customers/{customer_id}")
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(404, "Customer not found")
    txs = (
        db.query(Transaction)
        .options(joinedload(Transaction.customer))
        .filter(Transaction.customer_id == customer_id)
        .order_by(Transaction.created_at.desc())
        .all()
    )
    opps = db.query(RecoveryOpportunity).filter(RecoveryOpportunity.customer_id == customer_id).all()
    return {
        "customer": CustomerOut.model_validate(customer),
        "transactions": [serialize_tx(t) for t in txs],
        "opportunities": [opportunity_to_dict(o) for o in opps],
    }
