from sqlalchemy.orm import Session

from app.models import AgentAction, Customer, RecoveryOpportunity, Transaction
from app.services.scoring import score_bundle
from app.utils.calculations import utcnow


class RevenueAgent:
    def analyse_transaction(self, db: Session, tx: Transaction, previous_attempts: int = 0) -> dict:
        customer: Customer = tx.customer
        scored = score_bundle(
            successful_payments=customer.successful_payments,
            failed_payments=customer.failed_payments,
            lifetime_value=customer.lifetime_value,
            amount=tx.amount,
            failure_reason=tx.failure_reason,
            payment_method=tx.payment_method,
            created_at=tx.created_at,
            previous_recovery_attempts=previous_attempts,
        )
        tx.recovery_probability = scored["recovery_probability"]
        return scored

    def record_scan(self, db: Session, transaction_count: int) -> AgentAction:
        action = AgentAction(
            opportunity_id=None,
            agent_name="Revenue Agent",
            action="analyse_ledger",
            decision="completed",
            risk_level="low",
            reason=f"Analysed {transaction_count} transactions for revenue leakage.",
            created_at=utcnow(),
        )
        db.add(action)
        return action


revenue_agent = RevenueAgent()
