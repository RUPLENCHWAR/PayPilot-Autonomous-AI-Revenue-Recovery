from sqlalchemy.orm import Session

from app.models import AgentAction, Customer, RecoveryOpportunity, Transaction
from app.config import get_settings
from app.services.ai_service import recommend_recovery
from app.utils.calculations import utcnow


class RecoveryAgent:
    def build_payload(self, customer: Customer, tx: Transaction, history: list[Transaction], probability: float) -> dict:
        recent = sorted(history, key=lambda t: t.created_at, reverse=True)[:8]
        return {
            "recovery_strategy": self._strategy(tx, probability, customer),
            "customer": {
                "name": customer.name,
                "email": customer.email,
                "successful_payments": customer.successful_payments,
                "failed_payments": customer.failed_payments,
                "lifetime_value": customer.lifetime_value,
                "recovery_score": customer.recovery_score,
            },
            "transaction": {
                "id": tx.id,
                "external_transaction_id": tx.external_transaction_id,
                "amount": tx.amount,
                "currency": tx.currency,
                "status": tx.status,
                "payment_method": tx.payment_method,
                "failure_reason": tx.failure_reason,
            },
            "payment_history": [
                {
                    "amount": h.amount,
                    "status": h.status,
                    "failure_reason": h.failure_reason,
                    "created_at": h.created_at.isoformat(),
                }
                for h in recent
            ],
            "recovery_probability": probability,
            "merchant_policy": {
                "autonomous_amount_limit": get_settings().effective_autonomous_amount_limit,
                "autonomous_enabled": get_settings().autonomous_enabled,
                "currency": "INR",
                "refunds_never_autonomous": True,
            },
        }

    def recommend(self, db: Session, customer: Customer, tx: Transaction, probability: float) -> dict:
        history = (
            db.query(Transaction)
            .filter(Transaction.customer_id == customer.id)
            .all()
        )
        payload = self.build_payload(customer, tx, history, probability)
        return recommend_recovery(payload)

    def _strategy(self, tx, probability: float, customer) -> str:
        reason = (tx.failure_reason or "").lower()
        if probability < 0.35:
            return "no_action"
        if reason in {"card_expired", "account_blocked", "do_not_honor"}:
            return "payment_method_change"
        if tx.amount > 25000:
            return "human_review"
        if reason in {"bank_timeout", "network_error", "issuer_unavailable", "authentication_timeout"} and customer.successful_payments >= 3:
            return "payment_link"
        if reason == "abandoned":
            return "reminder"
        if probability >= 0.72:
            return "payment_link"
        return "silent_retry"

    def record(self, db: Session, opportunity_id: int | None, recommendation: dict) -> AgentAction:
        action = AgentAction(
            opportunity_id=opportunity_id,
            agent_name="Recovery Agent",
            action=recommendation.get("recommended_action", "unknown"),
            decision=recommendation.get("decision", "unknown"),
            risk_level=recommendation.get("risk_level", "medium"),
            reason=recommendation.get("reason", ""),
            created_at=utcnow(),
        )
        db.add(action)
        return action


recovery_agent = RecoveryAgent()
