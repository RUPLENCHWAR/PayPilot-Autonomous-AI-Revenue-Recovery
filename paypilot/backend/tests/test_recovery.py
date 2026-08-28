from app.services.ai_service import recommend_recovery


def test_local_engine_does_not_invent_amount():
    payload = {
        "customer": {
            "name": "Priya Mehta",
            "email": "priya@example.com",
            "successful_payments": 8,
            "failed_payments": 1,
            "lifetime_value": 42000,
            "recovery_score": 0.84,
        },
        "transaction": {
            "id": 1,
            "external_transaction_id": "txn_1",
            "amount": 12999,
            "currency": "INR",
            "status": "failed",
            "payment_method": "upi",
            "failure_reason": "bank_timeout",
        },
        "payment_history": [],
        "recovery_probability": 0.88,
        "merchant_policy": {},
    }
    result = recommend_recovery(payload)
    assert result["expected_recovery"] == round(12999 * 0.88, 2)
    assert result["ai_source"] == "local_recovery_engine"
    assert result["recommended_action"] in {"retry", "payment_link", "reminder", "manual_review", "no_action"}
    assert "12999" in result["why_recover"] or "12,999" in result["why_recover"]
