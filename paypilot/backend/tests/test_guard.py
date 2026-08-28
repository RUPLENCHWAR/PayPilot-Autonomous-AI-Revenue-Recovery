from types import SimpleNamespace

from app.agents.guard_agent import RecoveryGuard


def _opp(amount: float, status: str = "pending", links=None):
    return SimpleNamespace(
        amount=amount,
        status=status,
        customer_id=1,
        payment_links=links or [],
    )


def test_low_amount_auto_approved():
    guard = RecoveryGuard()
    result = guard.evaluate(_opp(4999), "payment_link", "low")
    assert result["auto_approved"] is True
    assert result["requires_approval"] is False
    assert result["policy_label"] == "AUTO APPROVED"


def test_amount_above_autonomous_limit():
    guard = RecoveryGuard()
    result = guard.evaluate(_opp(24999), "payment_link", "low")
    assert result["requires_approval"] is True
    assert result["policy_label"] == "HUMAN APPROVAL REQUIRED"


def test_high_risk_requires_approval():
    guard = RecoveryGuard()
    result = guard.evaluate(_opp(1999), "payment_link", "high")
    assert result["requires_approval"] is True


def test_refund_never_autonomous():
    guard = RecoveryGuard()
    result = guard.evaluate(_opp(500), "refund", "low")
    assert result["allowed"] is False
    assert result["requires_approval"] is True


def test_duplicate_recovery_blocked():
    guard = RecoveryGuard()
    link = SimpleNamespace(status="created")
    result = guard.evaluate(_opp(1999, status="executed", links=[link]), "payment_link", "low")
    assert result["policy_label"] == "DUPLICATE BLOCKED"
    assert result["allowed"] is False
