from datetime import datetime
from typing import Optional

from app.utils.calculations import classify_priority, expected_recovery, utcnow


TEMPORARY_FAILURES = {
    "insufficient_funds",
    "bank_timeout",
    "network_error",
    "issuer_unavailable",
    "authentication_timeout",
}

PERMANENT_FAILURES = {
    "card_expired",
    "account_blocked",
    "invalid_account",
    "do_not_honor",
}

METHOD_SCORES = {
    "upi": 0.12,
    "card": 0.06,
    "netbanking": 0.04,
    "wallet": 0.02,
    "emi": -0.04,
}


def recovery_probability(
    *,
    successful_payments: int,
    failed_payments: int,
    lifetime_value: float,
    amount: float,
    failure_reason: Optional[str],
    payment_method: Optional[str],
    created_at: Optional[datetime] = None,
    previous_recovery_attempts: int = 0,
    now: Optional[datetime] = None,
) -> float:
    """Demo recovery scoring model. Transparent, not scientifically validated."""
    score = 0.38

    score += min(successful_payments, 12) * 0.035
    score -= min(failed_payments, 8) * 0.045
    score += min(lifetime_value / 100000.0, 0.14)

    if amount >= 24999:
        score += 0.08
    elif amount >= 8499:
        score += 0.05
    elif amount < 999:
        score -= 0.04

    reason = (failure_reason or "").lower()
    if reason in TEMPORARY_FAILURES:
        score += 0.16
    elif reason in PERMANENT_FAILURES:
        score -= 0.22
    elif reason == "abandoned":
        score += 0.10
    elif reason:
        score += 0.02

    method = (payment_method or "").lower()
    score += METHOD_SCORES.get(method, 0.0)

    current = now or utcnow()
    if created_at:
        age_days = max((current - created_at).total_seconds() / 86400.0, 0)
        if age_days <= 3:
            score += 0.08
        elif age_days <= 14:
            score += 0.03
        elif age_days > 45:
            score -= 0.10

    score -= min(previous_recovery_attempts, 4) * 0.08

    return round(min(max(score, 0.05), 0.97), 2)


def score_bundle(**kwargs) -> dict:
    probability = recovery_probability(**kwargs)
    amount = float(kwargs["amount"])
    return {
        "recovery_probability": probability,
        "priority": classify_priority(probability),
        "expected_recovery": expected_recovery(amount, probability),
        "model": "demo_recovery_scoring_v1",
    }
