import json
from typing import Any, Optional

from app.config import get_settings
from app.services.scoring import TEMPORARY_FAILURES, PERMANENT_FAILURES


SYSTEM_PROMPT = """You are PayPilot, an autonomous revenue recovery agent for Indian merchants using Razorpay.
You reason only over the provided JSON. Never invent transaction amounts, IDs, or customer facts.
Return strict JSON with keys:
decision, recommended_action, recovery_strategy, recovery_probability, expected_recovery, risk_level, reason, customer_message, why_customer, why_recover, why_action
decision must be recover or no_action.
recommended_action must be one of: retry, payment_link, reminder, manual_review, no_action.
risk_level must be low, medium, or high.
recovery_probability must match the provided score unless you have a documented reason to adjust within 0.05.
"""


def _local_recommendation(payload: dict[str, Any]) -> dict[str, Any]:
    customer = payload["customer"]
    tx = payload["transaction"]
    probability = float(payload["recovery_probability"])
    amount = float(tx["amount"])
    expected = round(amount * probability, 2)
    reason = (tx.get("failure_reason") or "").lower()
    successes = int(customer.get("successful_payments") or 0)
    failures = int(customer.get("failed_payments") or 0)
    ltv = float(customer.get("lifetime_value") or 0)

    if probability < 0.35 or reason in PERMANENT_FAILURES and successes < 2:
        decision = "no_action"
        action = "manual_review" if amount >= 8499 else "no_action"
        risk = "high"
    elif reason in PERMANENT_FAILURES:
        decision = "recover"
        action = "manual_review"
        risk = "high"
    elif amount > 24999:
        decision = "recover"
        action = "payment_link"
        risk = "medium"
    elif reason in TEMPORARY_FAILURES and successes >= 3:
        decision = "recover"
        action = "payment_link" if amount >= 1999 else "retry"
        risk = "low"
    elif reason in ("abandoned",) or tx.get("status") == "abandoned":
        decision = "recover"
        action = "reminder" if amount < 1999 else "payment_link"
        risk = "low"
    elif probability >= 0.6:
        decision = "recover"
        action = "payment_link"
        risk = "low" if probability >= 0.8 else "medium"
    else:
        decision = "recover"
        action = "reminder"
        risk = "medium"

    strategy = payload.get("recovery_strategy") or action
    if action == "retry" and amount > 10000:
        action = "payment_link"
        risk = "medium"

    why_customer = (
        f"{customer['name']} has completed {successes} successful payment(s) and "
        f"{failures} failed payment(s), with lifetime value of ₹{ltv:,.0f}."
    )
    if successes >= 5:
        why_customer += " Strong payment history supports outreach."
    elif successes <= 1:
        why_customer += " Thin payment history increases recovery uncertainty."

    if reason in TEMPORARY_FAILURES:
        why_recover = (
            f"The current ₹{amount:,.0f} transaction failed due to '{reason}', which often indicates a temporary issuer or funds issue rather than a lost customer."
        )
    elif reason in PERMANENT_FAILURES:
        why_recover = (
            f"Failure reason '{reason}' looks more persistent. Recovery should be cautious and may need a different instrument."
        )
    elif tx.get("status") == "abandoned":
        why_recover = "The checkout was abandoned before capture, so a timely reminder or payment link can still convert."
    else:
        why_recover = f"This ₹{amount:,.0f} payment is still unpaid and sits in a recoverable status."

    action_copy = {
        "payment_link": "Creating a Razorpay payment link is lower risk than silent retries and lets the customer complete payment on a fresh checkout.",
        "retry": "A single retry is reasonable because the failure looks transient and the amount is within a low-friction range.",
        "reminder": "A reminder is the lightest-touch action while we avoid aggressive charging.",
        "manual_review": "The risk profile needs a human before any collection attempt.",
        "no_action": "Expected recovery is too weak or the failure looks permanent; automated collection would waste attempts.",
    }
    why_action = action_copy[action]

    customer_message = (
        f"Hi {customer['name'].split()[0]}, your payment of ₹{amount:,.0f} did not go through. "
        "You can complete it securely using the link from PayPilot / Razorpay."
    )
    if action in ("no_action", "manual_review"):
        customer_message = "No customer message will be sent until a human reviews this case."

    reason_text = (
        f"Demo scoring model assigned recovery probability {probability:.0%}. "
        f"Recommended '{action}' because of payment history, amount, and failure reason '{reason or 'n/a'}'."
    )

    return {
        "decision": decision,
        "recommended_action": action,
        "recovery_strategy": strategy,
        "recovery_probability": probability,
        "expected_recovery": expected,
        "risk_level": risk,
        "reason": reason_text,
        "customer_message": customer_message,
        "why_customer": why_customer,
        "why_recover": why_recover,
        "why_action": why_action,
        "ai_source": "local_recovery_engine",
    }


def _openai_recommendation(payload: dict[str, Any]) -> Optional[dict[str, Any]]:
    settings = get_settings()
    if not settings.openai_configured:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(payload)},
            ],
        )
        content = response.choices[0].message.content or "{}"
        data = json.loads(content)
        required = [
            "decision",
            "recommended_action",
            "recovery_strategy",
            "recovery_probability",
            "expected_recovery",
            "risk_level",
            "reason",
            "customer_message",
            "why_customer",
            "why_recover",
            "why_action",
        ]
        if not all(k in data for k in required):
            return None
        data["recovery_probability"] = float(payload["recovery_probability"])
        data["expected_recovery"] = round(float(payload["transaction"]["amount"]) * data["recovery_probability"], 2)
        data["ai_source"] = "openai"
        return data
    except Exception:
        return None


def recommend_recovery(payload: dict[str, Any]) -> dict[str, Any]:
    llm = _openai_recommendation(payload)
    if llm:
        return llm
    return _local_recommendation(payload)
