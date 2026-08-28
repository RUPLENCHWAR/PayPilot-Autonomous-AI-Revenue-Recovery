from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.database import get_db
from app.models import AgentAction, PaymentLink, RecoveryOpportunity, Transaction
from app.schemas import CommandRequest, CommandResponse, ExecuteResponse
from app.services.analytics_service import compute_metrics
from app.services.razorpay_service import RazorpayError
from app.services.recovery_service import (
    analyse_opportunity,
    approve_opportunity,
    execute_opportunity,
    opportunity_to_dict,
    simulate_outcome,
)

router = APIRouter(tags=["recovery"])


@router.get("/recovery/opportunities")
def list_opportunities(status: str | None = None, db: Session = Depends(get_db)):
    query = db.query(RecoveryOpportunity).order_by(RecoveryOpportunity.expected_recovery.desc())
    if status:
        query = query.filter(RecoveryOpportunity.status == status)
    rows = query.all()
    return {"items": [opportunity_to_dict(o) for o in rows], "count": len(rows)}


@router.get("/recovery/opportunities/{opportunity_id}")
def get_opportunity(opportunity_id: int, db: Session = Depends(get_db)):
    opp = (
        db.query(RecoveryOpportunity)
        .options(
            joinedload(RecoveryOpportunity.customer),
            joinedload(RecoveryOpportunity.transaction),
            joinedload(RecoveryOpportunity.payment_links),
            joinedload(RecoveryOpportunity.actions),
        )
        .filter(RecoveryOpportunity.id == opportunity_id)
        .first()
    )
    if not opp:
        raise HTTPException(404, "Opportunity not found")
    return {
        "opportunity": opportunity_to_dict(opp),
        "payment_links": sorted(opp.payment_links, key=lambda x: x.created_at, reverse=True),
        "actions": sorted(opp.actions, key=lambda a: a.created_at, reverse=True),
        "transaction": opp.transaction,
        "customer": opp.customer,
    }


@router.post("/recovery/{opportunity_id}/analyze")
def analyze(opportunity_id: int, db: Session = Depends(get_db)):
    try:
        return analyse_opportunity(db, opportunity_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.post("/recovery/{opportunity_id}/execute", response_model=ExecuteResponse)
def execute(opportunity_id: int, db: Session = Depends(get_db)):
    try:
        result = execute_opportunity(db, opportunity_id)
        return result
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(409, str(exc)) from exc
    except RazorpayError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc


@router.post("/recovery/{opportunity_id}/approve", response_model=ExecuteResponse)
def approve(opportunity_id: int, db: Session = Depends(get_db)):
    try:
        return approve_opportunity(db, opportunity_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(409, str(exc)) from exc
    except RazorpayError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc


@router.post("/recovery/{opportunity_id}/simulate-success")
def simulate_success(opportunity_id: int, db: Session = Depends(get_db)):
    try:
        return simulate_outcome(db, opportunity_id, True)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/recovery/{opportunity_id}/simulate-failure")
def simulate_failure(opportunity_id: int, db: Session = Depends(get_db)):
    try:
        return simulate_outcome(db, opportunity_id, False)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.get("/agent/activity")
def agent_activity(db: Session = Depends(get_db)):
    rows = db.query(AgentAction).order_by(AgentAction.created_at.desc()).limit(80).all()
    summary = {
        "revenue_analysed": db.query(Transaction).count(),
        "opportunities": db.query(RecoveryOpportunity).count(),
        "recommendations": db.query(AgentAction).filter(AgentAction.agent_name == "Recovery Agent").count(),
        "auto_approved": db.query(AgentAction).filter(AgentAction.decision == "auto_approved").count(),
        "needs_approval": db.query(AgentAction).filter(AgentAction.decision == "human_approval_required").count(),
        "payment_links": db.query(PaymentLink).count(),
    }
    return {"items": rows, "summary": summary}


@router.post("/command", response_model=CommandResponse)
def command_bar(body: CommandRequest, db: Session = Depends(get_db)):
    q = body.query.strip().lower()
    metrics = compute_metrics(db)
    settings = get_settings()

    if "biggest" in q or "leak" in q or "high-value failed" in q or "high value" in q:
        opps = (
            db.query(RecoveryOpportunity)
            .filter(RecoveryOpportunity.status.in_(["pending", "approved", "executed"]))
            .order_by(RecoveryOpportunity.amount.desc())
            .limit(8)
            .all()
        )
        return CommandResponse(
            intent="revenue_leaks",
            title="Largest unpaid recoverable transactions",
            answer=(
                f"Revenue at risk is ₹{metrics['revenue_at_risk']:,.0f}. "
                f"Expected recoverable revenue (probability-weighted) is ₹{metrics['recoverable_revenue']:,.0f}."
            ),
            data={"opportunities": [opportunity_to_dict(o) for o in opps]},
        )

    if "why" in q and "drop" in q:
        return CommandResponse(
            intent="revenue_drop",
            title="Why revenue is leaking",
            answer=(
                f"{metrics['failed_count']} failed/abandoned payments sit unpaid. "
                "Temporary issuer issues (timeouts, insufficient funds) are typically recoverable; "
                "blocked or expired instruments usually need a new payment method."
            ),
            data={"metrics": metrics},
        )

    if "how much" in q or "can we recover" in q or "recoverable" in q:
        return CommandResponse(
            intent="recoverable_amount",
            title="How much can we recover?",
            answer=(
                f"Expected recoverable revenue is ₹{metrics['recoverable_revenue']:,.0f} "
                f"from {metrics['opportunity_count']} opportunities. "
                f"This is not guaranteed — it is amount × demo recovery probability. "
                f"Actual recovered revenue so far is ₹{metrics['recovered_revenue']:,.0f}."
            ),
            data={"metrics": metrics},
        )

    if "highest priority" in q or "recover the highest" in q:
        opp = (
            db.query(RecoveryOpportunity)
            .filter(RecoveryOpportunity.status == "pending")
            .order_by(RecoveryOpportunity.recovery_probability.desc(), RecoveryOpportunity.amount.desc())
            .first()
        )
        if not opp:
            return CommandResponse(intent="recover_priority", title="No pending opportunity", answer="No pending recovery opportunities.")
        if not body.confirm:
            return CommandResponse(
                intent="recover_priority",
                title="Confirm recovery",
                answer=(
                    f"Highest priority pending case is opportunity #{opp.id} for ₹{opp.amount:,.0f} "
                    f"(probability {opp.recovery_probability:.0%}). Confirm to run RecoveryGuard and execute."
                ),
                requires_confirmation=True,
                data={"opportunity": opportunity_to_dict(opp)},
            )
        try:
            result = execute_opportunity(db, opp.id)
        except (ValueError, PermissionError, RazorpayError) as exc:
            return CommandResponse(intent="recover_priority", title="Execution blocked", answer=str(exc), data={})
        return CommandResponse(
            intent="recover_priority",
            title="Recovery execution attempted",
            answer=result.get("message", "Done"),
            data={"result": {"ok": result.get("ok"), "requires_approval": result.get("requires_approval")}},
        )

    return CommandResponse(
        intent="help",
        title="PayPilot command bar",
        answer=(
            "Try: 'Show me the biggest revenue leaks', 'Why did revenue drop?', "
            "'How much revenue can we recover?', or 'Recover the highest priority customer'."
        ),
        data={"mode": settings.effective_razorpay_mode},
    )
