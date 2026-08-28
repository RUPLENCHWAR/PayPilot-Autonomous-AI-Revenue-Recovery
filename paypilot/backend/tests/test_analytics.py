from app.services.scoring import recovery_probability
from app.utils.calculations import expected_recovery, classify_priority
from app.services.analytics_service import RECOVERABLE_STATUSES


def test_high_probability_customer():
    score = recovery_probability(
        successful_payments=10,
        failed_payments=1,
        lifetime_value=80000,
        amount=12999,
        failure_reason="bank_timeout",
        payment_method="upi",
        previous_recovery_attempts=0,
    )
    assert score >= 0.80
    assert classify_priority(score) == "HIGH"


def test_low_probability_customer():
    score = recovery_probability(
        successful_payments=0,
        failed_payments=6,
        lifetime_value=499,
        amount=8499,
        failure_reason="account_blocked",
        payment_method="emi",
        previous_recovery_attempts=3,
    )
    assert score < 0.60
    assert classify_priority(score) == "LOW"


def test_expected_recovery():
    assert expected_recovery(10000, 0.8) == 8000
    assert expected_recovery(4999, 0.5) == 2499.5


def test_recoverable_is_not_all_failed():
    assert "refunded" not in RECOVERABLE_STATUSES
    assert "captured" not in RECOVERABLE_STATUSES
