from collections import defaultdict
from datetime import timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import AgentAction, Customer, RecoveryOpportunity, Transaction
from app.utils.calculations import utcnow


RECOVERABLE_STATUSES = {"failed", "abandoned", "pending"}


def compute_metrics(db: Session) -> dict:
    captured = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0.0))
        .filter(Transaction.status == "captured")
        .scalar()
        or 0.0
    )
    recovered_tx = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0.0))
        .filter(Transaction.recovered.is_(True))
        .scalar()
        or 0.0
    )
    at_risk = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0.0))
        .filter(
            Transaction.status.in_(list(RECOVERABLE_STATUSES)),
            Transaction.recovered.is_(False),
        )
        .scalar()
        or 0.0
    )
    recoverable = (
        db.query(func.coalesce(func.sum(RecoveryOpportunity.expected_recovery), 0.0))
        .filter(
            RecoveryOpportunity.status.in_(["pending", "approved", "executed"]),
        )
        .scalar()
        or 0.0
    )
    eligible_amount = (
        db.query(func.coalesce(func.sum(RecoveryOpportunity.amount), 0.0))
        .filter(
            RecoveryOpportunity.status.in_(["pending", "approved", "executed", "recovered"]),
        )
        .scalar()
        or 0.0
    )
    recovery_rate = (recovered_tx / eligible_amount) if eligible_amount else 0.0

    open_opps = (
        db.query(RecoveryOpportunity)
        .filter(RecoveryOpportunity.status.in_(["pending", "approved", "executed"]))
        .all()
    )
    if open_opps:
        weighted = sum(o.recovery_probability * o.amount for o in open_opps)
        total_amt = sum(o.amount for o in open_opps) or 1
        confidence = weighted / total_amt
    else:
        confidence = 0.0

    pending_approvals = (
        db.query(func.count(RecoveryOpportunity.id))
        .filter(
            RecoveryOpportunity.status == "pending",
            RecoveryOpportunity.amount > get_settings().autonomous_amount_limit,
        )
        .scalar()
        or 0
    )
    auto_approved = (
        db.query(func.count(AgentAction.id))
        .filter(AgentAction.agent_name == "RecoveryGuard", AgentAction.decision == "auto_approved")
        .scalar()
        or 0
    )

    return {
        "total_revenue": round(float(captured), 2),
        "revenue_at_risk": round(float(at_risk), 2),
        "recoverable_revenue": round(float(recoverable), 2),
        "recovered_revenue": round(float(recovered_tx), 2),
        "recovery_rate": round(float(recovery_rate), 4),
        "recovery_confidence": round(float(confidence), 4),
        "opportunity_count": db.query(func.count(RecoveryOpportunity.id))
        .filter(RecoveryOpportunity.status != "rejected")
        .scalar()
        or 0,
        "pending_approvals": int(pending_approvals),
        "auto_approved_count": int(auto_approved),
        "transaction_count": db.query(func.count(Transaction.id)).scalar() or 0,
        "failed_count": db.query(func.count(Transaction.id))
        .filter(Transaction.status.in_(["failed", "abandoned"]))
        .scalar()
        or 0,
        "customer_count": db.query(func.count(Customer.id)).scalar() or 0,
    }


def revenue_trend(db: Session, days: int = 14) -> list[dict]:
    start = utcnow() - timedelta(days=days)
    rows = (
        db.query(Transaction)
        .filter(Transaction.created_at >= start)
        .all()
    )
    buckets: dict[str, dict] = defaultdict(lambda: {"captured": 0.0, "failed": 0.0, "recovered": 0.0})
    for tx in rows:
        key = tx.created_at.date().isoformat()
        if tx.status == "captured":
            buckets[key]["captured"] += tx.amount
        if tx.status in ("failed", "abandoned") and not tx.recovered:
            buckets[key]["failed"] += tx.amount
        if tx.recovered:
            buckets[key]["recovered"] += tx.amount
    points = []
    for i in range(days, -1, -1):
        day = (utcnow() - timedelta(days=i)).date().isoformat()
        data = buckets.get(day, {"captured": 0.0, "failed": 0.0, "recovered": 0.0})
        points.append({"date": day, **{k: round(v, 2) for k, v in data.items()}})
    return points


def failure_breakdown(db: Session) -> list[dict]:
    rows = (
        db.query(
            Transaction.failure_reason,
            func.count(Transaction.id),
            func.coalesce(func.sum(Transaction.amount), 0.0),
        )
        .filter(
            Transaction.status.in_(["failed", "abandoned"]),
            Transaction.recovered.is_(False),
        )
        .group_by(Transaction.failure_reason)
        .all()
    )
    result = []
    for reason, count, amount in rows:
        result.append(
            {
                "reason": reason or "unknown",
                "count": int(count),
                "amount": round(float(amount), 2),
            }
        )
    result.sort(key=lambda x: x["amount"], reverse=True)
    return result


def top_recoverable_customers(db: Session, limit: int = 6) -> list[dict]:
    rows = (
        db.query(
            Customer.id,
            Customer.name,
            Customer.email,
            Customer.recovery_score,
            func.coalesce(func.sum(RecoveryOpportunity.expected_recovery), 0.0),
            func.coalesce(func.sum(RecoveryOpportunity.amount), 0.0),
        )
        .join(RecoveryOpportunity, RecoveryOpportunity.customer_id == Customer.id)
        .filter(RecoveryOpportunity.status.in_(["pending", "approved", "executed"]))
        .group_by(Customer.id)
        .order_by(func.sum(RecoveryOpportunity.expected_recovery).desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r[0],
            "name": r[1],
            "email": r[2],
            "recovery_score": r[3],
            "expected_recovery": round(float(r[4]), 2),
            "failed_amount": round(float(r[5]), 2),
        }
        for r in rows
    ]
