from sqlalchemy.orm import Session, joinedload

from app.agents.guard_agent import guard_agent
from app.agents.recovery_agent import recovery_agent
from app.agents.revenue_agent import revenue_agent
from app.config import get_settings
from app.models import AgentAction, Customer, PaymentLink, RecoveryOpportunity, Transaction
from app.services.razorpay_service import RazorpayError, razorpay_service
from app.services.scoring import score_bundle
from app.utils.calculations import utcnow
from app.utils.security import unique_reference


RECOVERABLE_STATUSES = {"failed", "abandoned", "pending"}


def opportunity_to_dict(opp: RecoveryOpportunity) -> dict:
    tx = opp.transaction
    customer = opp.customer
    return {
        "id": opp.id,
        "transaction_id": opp.transaction_id,
        "customer_id": opp.customer_id,
        "amount": opp.amount,
        "recovery_probability": opp.recovery_probability,
        "expected_recovery": opp.expected_recovery,
        "estimated_recovery_cost": opp.estimated_recovery_cost,
        "expected_net_recovery": opp.expected_net_recovery,
        "recovery_roi": opp.recovery_roi,
        "recovery_strategy": opp.recovery_strategy,
        "priority": opp.priority,
        "reason": opp.reason,
        "recommended_action": opp.recommended_action,
        "status": opp.status,
        "created_at": opp.created_at,
        "why_customer": opp.why_customer,
        "why_recover": opp.why_recover,
        "why_action": opp.why_action,
        "risk_level": opp.risk_level,
        "customer_message": opp.customer_message,
        "ai_source": opp.ai_source,
        "customer_name": customer.name if customer else None,
        "customer_email": customer.email if customer else None,
        "failure_reason": tx.failure_reason if tx else None,
        "payment_method": tx.payment_method if tx else None,
        "transaction_status": tx.status if tx else None,
    }


def refresh_customer_stats(db: Session, customer: Customer) -> None:
    txs = db.query(Transaction).filter(Transaction.customer_id == customer.id).all()
    captured = [t for t in txs if t.status == "captured" or t.recovered]
    failed = [t for t in txs if t.status in ("failed", "abandoned") and not t.recovered]
    total_paid = sum(t.amount for t in captured)
    customer.successful_payments = len(captured)
    customer.failed_payments = len(failed)
    customer.total_paid = round(total_paid, 2)
    customer.lifetime_value = round(total_paid, 2)
    customer.average_transaction_value = round(total_paid / len(captured), 2) if captured else 0
    if failed:
        scores = []
        for t in failed:
            attempts = (
                db.query(RecoveryOpportunity)
                .filter(RecoveryOpportunity.transaction_id == t.id, RecoveryOpportunity.status.in_(["executed", "recovered", "rejected"]))
                .count()
            )
            scored = score_bundle(
                successful_payments=customer.successful_payments,
                failed_payments=customer.failed_payments,
                lifetime_value=customer.lifetime_value,
                amount=t.amount,
                failure_reason=t.failure_reason,
                payment_method=t.payment_method,
                created_at=t.created_at,
                previous_recovery_attempts=attempts,
            )
            scores.append(scored["recovery_probability"])
        customer.recovery_score = round(sum(scores) / len(scores), 2)
    else:
        customer.recovery_score = round(min(0.4 + customer.successful_payments * 0.04, 0.95), 2)


def analyse_opportunity(db: Session, opportunity_id: int) -> dict:
    opp = (
        db.query(RecoveryOpportunity)
        .options(joinedload(RecoveryOpportunity.customer), joinedload(RecoveryOpportunity.transaction), joinedload(RecoveryOpportunity.payment_links))
        .filter(RecoveryOpportunity.id == opportunity_id)
        .first()
    )
    if not opp:
        raise ValueError("Opportunity not found")
    tx = opp.transaction
    customer = opp.customer
    attempts = (
        db.query(PaymentLink).filter(PaymentLink.opportunity_id == opp.id).count()
    )
    scored = revenue_agent.analyse_transaction(db, tx, previous_attempts=attempts)
    recommendation = recovery_agent.recommend(db, customer, tx, scored["recovery_probability"])
    opp.recovery_probability = scored["recovery_probability"]
    opp.expected_recovery = scored["expected_recovery"]
    opp.priority = scored["priority"]
    opp.recommended_action = recommendation["recommended_action"]
    strategy = recommendation.get("recovery_strategy") or recommendation["recommended_action"]
    estimated_cost = 25.0
    opp.estimated_recovery_cost = estimated_cost
    opp.expected_net_recovery = round(max(0, scored["expected_recovery"] - estimated_cost), 2)
    opp.recovery_roi = round(opp.expected_net_recovery / estimated_cost, 2) if estimated_cost else 0
    opp.recovery_strategy = strategy
    opp.reason = recommendation["reason"]
    opp.why_customer = recommendation["why_customer"]
    opp.why_recover = recommendation["why_recover"]
    opp.why_action = recommendation["why_action"]
    opp.risk_level = recommendation["risk_level"]
    opp.customer_message = recommendation["customer_message"]
    opp.ai_source = recommendation["ai_source"]
    tx.recovery_probability = scored["recovery_probability"]
    tx.recommended_action = recommendation["recommended_action"]
    recovery_agent.record(db, opp.id, recommendation)
    guard = guard_agent.evaluate(opp, recommendation["recommended_action"], recommendation["risk_level"])
    db.add(
        AgentAction(
            opportunity_id=opp.id,
            agent_name="RecoveryGuard",
            action="evaluate",
            decision=guard["policy_label"],
            risk_level=guard["risk_level"],
            reason=" ".join(guard["reasons"]),
            created_at=utcnow(),
        )
    )
    db.commit()
    db.refresh(opp)
    return {
        **recommendation,
        "recovery_probability": scored["recovery_probability"],
        "expected_recovery": scored["expected_recovery"],
        "guard": guard,
        "opportunity": opportunity_to_dict(opp),
    }


def _create_link(db: Session, opp: RecoveryOpportunity, approved: bool) -> PaymentLink:
    if not approved:
        raise PermissionError("Human approval is required before execution.")
    existing = (
        db.query(PaymentLink)
        .filter(PaymentLink.opportunity_id == opp.id, PaymentLink.status.in_(["created", "issued", "paid"]))
        .first()
    )
    if existing and opp.status in {"executed", "recovered"}:
        raise ValueError("A recovery payment link already exists for this opportunity.")

    settings = get_settings()
    reference_id = unique_reference("pp", opp.id)
    customer = opp.customer
    created = razorpay_service.create_payment_link(
        amount_inr=opp.amount,
        reference_id=reference_id,
        description=f"PayPilot recovery for {opp.transaction.external_transaction_id}",
        customer_name=customer.name,
        customer_email=customer.email,
        customer_phone=customer.phone,
        notes={
            "opportunity_id": str(opp.id),
            "transaction_id": str(opp.transaction_id),
            "source": "paypilot",
        },
    )
    link = PaymentLink(
        opportunity_id=opp.id,
        razorpay_link_id=created["id"],
        short_url=created["short_url"],
        amount=opp.amount,
        status="created",
        created_at=utcnow(),
        reference_id=reference_id,
        mode=created.get("mode") or settings.effective_razorpay_mode,
    )
    db.add(link)
    opp.status = "executed"
    db.add(
        AgentAction(
            opportunity_id=opp.id,
            agent_name="Razorpay Agent",
            action="create_payment_link",
            decision="created" if created.get("mode") == "test" else "demo_created",
            risk_level=opp.risk_level or "medium",
            reason=(
                f"Created Razorpay test payment link {created['id']}."
                if created.get("mode") == "test"
                else "Demo Mode — No real payment was created."
            ),
            created_at=utcnow(),
        )
    )
    db.commit()
    db.refresh(link)
    db.refresh(opp)
    return link


def execute_opportunity(db: Session, opportunity_id: int, *, force_approved: bool = False) -> dict:
    opp = (
        db.query(RecoveryOpportunity)
        .options(joinedload(RecoveryOpportunity.customer), joinedload(RecoveryOpportunity.transaction), joinedload(RecoveryOpportunity.payment_links))
        .filter(RecoveryOpportunity.id == opportunity_id)
        .first()
    )
    if not opp:
        raise ValueError("Opportunity not found")
    analysis = analyse_opportunity(db, opportunity_id)
    db.refresh(opp)
    guard = analysis["guard"]
    if not guard["allowed"] and guard["policy_label"] in {"BLOCKED", "DUPLICATE BLOCKED", "NO ACTION"}:
        raise PermissionError(guard["reasons"][0] if guard["reasons"] else "Action blocked by RecoveryGuard.")

    requires = guard["requires_approval"] and not force_approved and not (opp.status == "approved")
    auto = guard["auto_approved"] and not requires
    if requires:
        db.add(
            AgentAction(
                opportunity_id=opp.id,
                agent_name="RecoveryGuard",
                action="hold",
                decision="human_approval_required",
                risk_level=guard["risk_level"],
                reason=" ".join(guard["reasons"]),
                created_at=utcnow(),
            )
        )
        db.commit()
        return {
            "ok": False,
            "message": "HUMAN APPROVAL REQUIRED",
            "requires_approval": True,
            "auto_approved": False,
            "analysis": analysis,
            "opportunity": opportunity_to_dict(opp),
            "payment_link": None,
            "demo_mode": get_settings().effective_razorpay_mode == "demo",
            "razorpay_mode": get_settings().effective_razorpay_mode,
        }

    if auto:
        db.add(
            AgentAction(
                opportunity_id=opp.id,
                agent_name="RecoveryGuard",
                action="approve",
                decision="auto_approved",
                risk_level=guard["risk_level"],
                reason=" ".join(guard["reasons"]),
                created_at=utcnow(),
            )
        )
        db.commit()

    link = _create_link(db, opp, approved=True)
    db.refresh(opp)
    return {
        "ok": True,
        "message": "Demo Mode — No real payment was created."
        if link.mode == "demo"
        else "Razorpay test payment link created.",
        "requires_approval": False,
        "auto_approved": auto or force_approved,
        "analysis": analysis,
        "opportunity": opportunity_to_dict(opp),
        "payment_link": link,
        "demo_mode": link.mode == "demo",
        "razorpay_mode": get_settings().effective_razorpay_mode,
    }


def approve_opportunity(db: Session, opportunity_id: int) -> dict:
    opp = db.query(RecoveryOpportunity).filter(RecoveryOpportunity.id == opportunity_id).first()
    if not opp:
        raise ValueError("Opportunity not found")
    opp.status = "approved"
    db.add(
        AgentAction(
            opportunity_id=opp.id,
            agent_name="RecoveryGuard",
            action="approve",
            decision="human_approved",
            risk_level=opp.risk_level or "medium",
            reason="Operator approved this recovery action in the dashboard.",
            created_at=utcnow(),
        )
    )
    db.commit()
    return execute_opportunity(db, opportunity_id, force_approved=True)


def simulate_outcome(db: Session, opportunity_id: int, success: bool) -> dict:
    settings = get_settings()
    if settings.effective_razorpay_mode != "demo":
        raise PermissionError("Simulation is only available in DEMO MODE. Real Razorpay payments are confirmed by webhooks.")
    opp = (
        db.query(RecoveryOpportunity)
        .options(joinedload(RecoveryOpportunity.transaction), joinedload(RecoveryOpportunity.customer), joinedload(RecoveryOpportunity.payment_links))
        .filter(RecoveryOpportunity.id == opportunity_id)
        .first()
    )
    if not opp:
        raise ValueError("Opportunity not found")
    if opp.status == "recovered":
        raise ValueError("Recovered opportunities cannot be simulated again.")
    if opp.status == "rejected":
        raise ValueError("Rejected opportunities cannot be simulated.")
    link = (
        db.query(PaymentLink)
        .filter(PaymentLink.opportunity_id == opp.id)
        .order_by(PaymentLink.created_at.desc())
        .first()
    )
    if not link:
        raise ValueError("Create a demo payment link before simulating payment.")
    tx = opp.transaction
    if link.status == "paid":
        raise ValueError("This payment link has already been paid.")
    if success:
        link.status = "paid"
        opp.status = "recovered"
        tx.recovered = True
        tx.status = "captured"
        tx.failure_reason = None
        refresh_customer_stats(db, opp.customer)
        decision = "simulated_success"
        reason = "Demo payment marked successful. Recovered revenue updated. No real Razorpay settlement occurred."
    else:
        link.status = "expired"
        opp.status = "pending"
        tx.recovered = False
        decision = "simulated_failure"
        reason = "Demo payment marked failed. Opportunity remains recoverable."
    db.add(
        AgentAction(
            opportunity_id=opp.id,
            agent_name="Razorpay Agent",
            action="simulate_payment",
            decision=decision,
            risk_level="low",
            reason=reason,
            created_at=utcnow(),
        )
    )
    db.commit()
    db.refresh(opp)
    return {
        "ok": success,
        "message": reason,
        "opportunity": opportunity_to_dict(opp),
        "demo_mode": True,
        "razorpay_mode": "demo",
    }


def apply_webhook_payment(db: Session, *, reference_id: str | None, link_id: str | None, captured: bool, amount_paise: int | None) -> bool:
    query = db.query(PaymentLink)
    link = None
    if reference_id:
        link = query.filter(PaymentLink.reference_id == reference_id).first()
    if not link and link_id:
        link = db.query(PaymentLink).filter(PaymentLink.razorpay_link_id == link_id).first()
    if not link:
        return False
    opp = db.query(RecoveryOpportunity).filter(RecoveryOpportunity.id == link.opportunity_id).first()
    if not opp:
        return False
    tx = db.query(Transaction).filter(Transaction.id == opp.transaction_id).first()
    if captured:
        link.status = "paid"
        opp.status = "recovered"
        if tx:
            tx.recovered = True
            tx.status = "captured"
            tx.failure_reason = None
        refresh_customer_stats(db, opp.customer)
        reason = "Razorpay webhook: payment captured. Recovery marked complete."
        decision = "webhook_captured"
    else:
        link.status = "failed"
        reason = "Razorpay webhook: payment failed."
        decision = "webhook_failed"
    db.add(
        AgentAction(
            opportunity_id=opp.id,
            agent_name="Razorpay Agent",
            action="webhook",
            decision=decision,
            risk_level="low",
            reason=reason,
            created_at=utcnow(),
        )
    )
    db.commit()
    return True


def rebuild_opportunities(db: Session) -> int:
    created = 0
    txs = (
        db.query(Transaction)
        .options(joinedload(Transaction.customer))
        .filter(Transaction.status.in_(list(RECOVERABLE_STATUSES)), Transaction.recovered.is_(False))
        .all()
    )
    for tx in txs:
        existing = db.query(RecoveryOpportunity).filter(RecoveryOpportunity.transaction_id == tx.id).first()
        customer = tx.customer
        scored = score_bundle(
            successful_payments=customer.successful_payments,
            failed_payments=customer.failed_payments,
            lifetime_value=customer.lifetime_value,
            amount=tx.amount,
            failure_reason=tx.failure_reason,
            payment_method=tx.payment_method,
            created_at=tx.created_at,
            previous_recovery_attempts=0,
        )
        recommendation = recovery_agent.recommend(db, customer, tx, scored["recovery_probability"])
        tx.recovery_probability = scored["recovery_probability"]
        tx.recommended_action = recommendation["recommended_action"]
        if existing:
            continue
        opp = RecoveryOpportunity(
            transaction_id=tx.id,
            customer_id=customer.id,
            amount=tx.amount,
            recovery_probability=scored["recovery_probability"],
            expected_recovery=scored["expected_recovery"],
            estimated_recovery_cost=25.0,
            expected_net_recovery=round(max(0, scored["expected_recovery"] - 25.0), 2),
            recovery_roi=round(max(0, scored["expected_recovery"] - 25.0) / 25.0, 2),
            recovery_strategy=recommendation.get("recovery_strategy") or recommendation["recommended_action"],
            priority=scored["priority"],
            reason=recommendation["reason"],
            recommended_action=recommendation["recommended_action"],
            status="pending",
            created_at=utcnow(),
            why_customer=recommendation["why_customer"],
            why_recover=recommendation["why_recover"],
            why_action=recommendation["why_action"],
            risk_level=recommendation["risk_level"],
            customer_message=recommendation["customer_message"],
            ai_source=recommendation["ai_source"],
        )
        db.add(opp)
        created += 1
    db.commit()
    return created
