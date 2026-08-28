from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import get_settings, update_autonomy_settings
from app.database import get_db
from app.models import AgentAction, RecoveryOpportunity
from app.schemas import DashboardResponse, DashboardMetrics, HealthResponse, SettingsOut, AutonomyUpdate
from app.services import analytics_service
from app.services.recovery_service import opportunity_to_dict

router = APIRouter(tags=["dashboard"])


@router.get("/health", response_model=HealthResponse)
def health():
    settings = get_settings()
    return HealthResponse(
        status="ok",
        razorpay_mode=settings.effective_razorpay_mode,
        ai_mode="openai" if settings.openai_configured else "local",
        openai_configured=settings.openai_configured,
        razorpay_configured=settings.razorpay_configured,
    )


@router.get("/settings", response_model=SettingsOut)
def settings_view():
    settings = get_settings()
    return SettingsOut(
        razorpay_mode=settings.effective_razorpay_mode,
        razorpay_configured=settings.razorpay_configured,
        ai_mode="openai" if settings.openai_configured else "local",
        openai_configured=settings.openai_configured,
        autonomous_amount_limit=settings.effective_autonomous_amount_limit,
        webhook_configured=settings.webhook_secret_configured,
        frontend_url=settings.frontend_url,
    )


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(db: Session = Depends(get_db)):
    settings = get_settings()
    metrics = analytics_service.compute_metrics(db)
    metrics["razorpay_mode"] = settings.effective_razorpay_mode
    metrics["ai_mode"] = "openai" if settings.openai_configured else "local"
    recent = (
        db.query(AgentAction)
        .order_by(AgentAction.created_at.desc())
        .limit(12)
        .all()
    )
    opps = (
        db.query(RecoveryOpportunity)
        .filter(RecoveryOpportunity.status.in_(["pending", "approved", "executed"]))
        .order_by(RecoveryOpportunity.expected_recovery.desc())
        .limit(8)
        .all()
    )
    return DashboardResponse(
        metrics=DashboardMetrics(**metrics),
        trend=analytics_service.revenue_trend(db),
        failure_breakdown=analytics_service.failure_breakdown(db),
        recent_actions=recent,
        top_customers=analytics_service.top_recoverable_customers(db),
        opportunities=[opportunity_to_dict(o) for o in opps],
    )


@router.patch("/settings/autonomy")
def update_autonomy(body: AutonomyUpdate):
    update_autonomy_settings(body.autonomous_amount_limit, body.enabled)
    settings = get_settings()
    return {"autonomous_amount_limit": settings.effective_autonomous_amount_limit, "enabled": settings.autonomous_enabled}


@router.get("/recovery/simulator")
def recovery_simulator(limit: int = 10000, db: Session = Depends(get_db)):
    from app.services.recovery_service import opportunity_to_dict
    rows = db.query(RecoveryOpportunity).filter(RecoveryOpportunity.status.in_(["pending", "approved", "executed"])).all()
    current = get_settings().effective_autonomous_amount_limit
    def calc(lim):
        auto = [o for o in rows if o.amount <= lim and (o.risk_level or "low") == "low" and o.recommended_action not in {"refund", "partial_refund"}]
        approval = [o for o in rows if o not in auto]
        expected = sum(o.expected_recovery for o in auto)
        return len(auto), len(approval), round(expected, 2)
    ac, ap, ex = calc(limit)
    _, _, base = calc(current)
    return {"limit": limit, "current_limit": current, "autonomous_count": ac, "approval_count": ap, "expected_recovery": ex, "additional_expected_recovery": round(ex-base,2)}


@router.post("/recovery/scan")
def revenue_scan(db: Session = Depends(get_db)):
    from app.services.recovery_service import rebuild_opportunities
    created = rebuild_opportunities(db)
    return {"ok": True, "created": created, "message": "AI revenue scan completed."}
