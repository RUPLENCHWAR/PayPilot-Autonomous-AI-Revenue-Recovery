from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Customer, RecoveryOpportunity, Transaction
from app.services.recovery_service import rebuild_opportunities, refresh_customer_stats
from app.utils.calculations import utcnow


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)


def override_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_db
client = TestClient(app)


def _seed_case(db, *, successes: int, failures: int, amount: float, reason: str, method: str = "upi"):
    customer = Customer(
        external_customer_id=f"t_{successes}_{failures}_{amount}_{reason}",
        name="Test User",
        email="test@example.com",
        phone="+919999999999",
    )
    db.add(customer)
    db.flush()
    now = utcnow()
    for i in range(successes):
        db.add(
            Transaction(
                external_transaction_id=f"{customer.external_customer_id}_ok_{i}",
                customer_id=customer.id,
                amount=1999,
                currency="INR",
                status="captured",
                payment_method=method,
                created_at=now,
                recovered=False,
            )
        )
    fail = Transaction(
        external_transaction_id=f"{customer.external_customer_id}_fail",
        customer_id=customer.id,
        amount=amount,
        currency="INR",
        status="failed",
        payment_method=method,
        failure_reason=reason,
        created_at=now,
        recovered=False,
    )
    db.add(fail)
    db.commit()
    refresh_customer_stats(db, customer)
    db.commit()
    rebuild_opportunities(db)
    opp = db.query(RecoveryOpportunity).filter(RecoveryOpportunity.transaction_id == fail.id).first()
    return customer, fail, opp


def test_dashboard_endpoint():
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    body = response.json()
    assert "metrics" in body
    assert "total_revenue" in body["metrics"]


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_and_simulate_flow():
    db = TestingSession()
    _, _, opp = _seed_case(db, successes=8, failures=1, amount=4999, reason="bank_timeout")
    db.close()
    analysed = client.post(f"/api/recovery/{opp.id}/analyze")
    assert analysed.status_code == 200
    executed = client.post(f"/api/recovery/{opp.id}/execute")
    assert executed.status_code == 200
    body = executed.json()
    if body.get("requires_approval"):
        approved = client.post(f"/api/recovery/{opp.id}/approve")
        assert approved.status_code == 200
        body = approved.json()
    assert body.get("ok") is True
    success = client.post(f"/api/recovery/{opp.id}/simulate-success")
    assert success.status_code == 200
    assert success.json()["ok"] is True


def test_simulate_failure_flow():
    db = TestingSession()
    _, _, opp = _seed_case(db, successes=6, failures=1, amount=1999, reason="network_error")
    db.close()
    executed = client.post(f"/api/recovery/{opp.id}/execute")
    assert executed.status_code == 200
    body = executed.json()
    if body.get("requires_approval"):
        body = client.post(f"/api/recovery/{opp.id}/approve").json()
    failed = client.post(f"/api/recovery/{opp.id}/simulate-failure")
    assert failed.status_code == 200
    assert failed.json()["ok"] is False
