from typing import Optional

from app.config import get_settings
from app.models import PaymentLink, RecoveryOpportunity


REFUND_ACTIONS = {"refund", "partial_refund"}
HIGH_RISK_ACTIONS = {"retry", "refund", "partial_refund"}


class RecoveryGuard:
    def evaluate(
        self,
        opportunity: RecoveryOpportunity,
        recommended_action: str,
        risk_level: str,
        existing_links: Optional[list[PaymentLink]] = None,
    ) -> dict:
        settings = get_settings()
        reasons: list[str] = []
        action = (recommended_action or "").lower()
        risk = (risk_level or "medium").lower()
        amount = float(opportunity.amount)

        if not settings.autonomous_enabled and action not in {"manual_review", "no_action"}:
            return {"allowed": False, "requires_approval": True, "auto_approved": False, "risk_level": risk, "reasons": ["Autonomous recovery is disabled by merchant policy."], "policy_label": "HUMAN APPROVAL"}

        if opportunity.status in {"recovered", "rejected"}:
            return {
                "allowed": False,
                "requires_approval": False,
                "auto_approved": False,
                "risk_level": risk,
                "reasons": [f"Opportunity is already {opportunity.status}."],
                "policy_label": "BLOCKED",
            }

        if action in REFUND_ACTIONS:
            reasons.append("Refund actions never execute autonomously.")
            return {
                "allowed": False,
                "requires_approval": True,
                "auto_approved": False,
                "risk_level": "high",
                "reasons": reasons,
                "policy_label": "HUMAN APPROVAL REQUIRED",
            }

        if action in {"no_action"}:
            reasons.append("Recommended action is no_action; nothing will be sent to Razorpay.")
            return {
                "allowed": False,
                "requires_approval": False,
                "auto_approved": False,
                "risk_level": risk,
                "reasons": reasons,
                "policy_label": "NO ACTION",
            }

        active_links = [
            link
            for link in (existing_links or opportunity.payment_links)
            if link.status in {"created", "issued", "paid"}
        ]
        if active_links and opportunity.status in {"executed", "recovered"}:
            reasons.append("A payment link already exists for this opportunity.")
            return {
                "allowed": False,
                "requires_approval": False,
                "auto_approved": False,
                "risk_level": risk,
                "reasons": reasons,
                "policy_label": "DUPLICATE BLOCKED",
            }

        if amount <= 0:
            reasons.append("Amount must be greater than zero.")
            return {
                "allowed": False,
                "requires_approval": False,
                "auto_approved": False,
                "risk_level": "high",
                "reasons": reasons,
                "policy_label": "BLOCKED",
            }

        if not opportunity.customer_id:
            reasons.append("Customer is missing.")
            return {
                "allowed": False,
                "requires_approval": False,
                "auto_approved": False,
                "risk_level": "high",
                "reasons": reasons,
                "policy_label": "BLOCKED",
            }

        requires_approval = False
        if risk == "high" or action in HIGH_RISK_ACTIONS and amount > settings.effective_autonomous_amount_limit:
            requires_approval = True
            reasons.append("High-risk actions always require human approval.")
        if amount > settings.effective_autonomous_amount_limit:
            requires_approval = True
            reasons.append(
                f"Amount ₹{amount:,.0f} exceeds the autonomous limit of ₹{settings.effective_autonomous_amount_limit:,}."
            )
        if action == "manual_review":
            requires_approval = True
            reasons.append("manual_review cannot be executed without a human.")

        if not requires_approval and risk == "low" and amount <= settings.effective_autonomous_amount_limit:
            reasons.append(
                f"Low-risk {action} for ₹{amount:,.0f} is within the autonomous policy (≤ ₹{settings.effective_autonomous_amount_limit:,})."
            )
            return {
                "allowed": True,
                "requires_approval": False,
                "auto_approved": True,
                "risk_level": risk,
                "reasons": reasons,
                "policy_label": "AUTO APPROVED",
            }

        if requires_approval:
            return {
                "allowed": True,
                "requires_approval": True,
                "auto_approved": False,
                "risk_level": risk,
                "reasons": reasons,
                "policy_label": "HUMAN APPROVAL REQUIRED",
            }

        reasons.append("Policy allows execution after explicit confirmation.")
        return {
            "allowed": True,
            "requires_approval": True,
            "auto_approved": False,
            "risk_level": risk,
            "reasons": reasons,
            "policy_label": "HUMAN APPROVAL REQUIRED",
        }


guard_agent = RecoveryGuard()
