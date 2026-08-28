from datetime import timedelta
from hashlib import sha256

from sqlalchemy.orm import Session

from app.models import AgentAction, Customer, PaymentLink, RecoveryOpportunity, Transaction
from app.services.recovery_service import rebuild_opportunities, refresh_customer_stats
from app.utils.calculations import utcnow


AMOUNTS = [499, 999, 1499, 1999, 2499, 4999, 8499, 12999, 24999, 49999]
METHODS = ["upi", "card", "netbanking", "wallet", "emi"]
FAILURES = [
    "insufficient_funds",
    "bank_timeout",
    "network_error",
    "issuer_unavailable",
    "authentication_timeout",
    "card_expired",
    "account_blocked",
    "abandoned",
]

CUSTOMER_SEEDS = [
    ("Priya Mehta", "priya.mehta@nimbuslabs.in", "strong", "UPI SaaS founder with a long successful history"),
    ("Arjun Kapoor", "arjun.kapoor@mailinator.com", "weak", "Repeated failures, low trust"),
    ("Neha Sharma", "neha.sharma@pixelcraft.co", "strong", "Agency retainer, high LTV"),
    ("Rohan Iyer", "rohan.iyer@coastalapps.in", "mixed", "Mostly successful with one high-value timeout"),
    ("Ananya Reddy", "ananya.reddy@bloomretail.in", "strong", "D2C brand, UPI heavy"),
    ("Vikram Singh", "vikram.singh@northpeak.io", "weak", "New customer, expired card"),
    ("Meera Nair", "meera.nair@keralahost.in", "strong", "Hosting invoices always paid"),
    ("Kabir Joshi", "kabir.joshi@urbanbite.in", "mixed", "Food-tech, occasional insufficient funds"),
    ("Ishita Banerjee", "ishita.b@designyard.co", "strong", "Design studio annual plan"),
    ("Aditya Rao", "aditya.rao@quantify.in", "weak", "Blocked account pattern"),
    ("Sana Qureshi", "sana.q@atelierwest.in", "strong", "Boutique, loyal card payer"),
    ("Dev Patel", "dev.patel@stackmint.dev", "mixed", "Devtools seat expansion failed once"),
    ("Lavanya Krishnan", "lavanya.k@chennaispace.in", "strong", "Coworking memberships"),
    ("Harsh Vardhan", "harsh.v@rapidcart.in", "weak", "COD-heavy merchant, poor card history"),
    ("Tara Menon", "tara.menon@leafwell.in", "strong", "Wellness subscriptions"),
    ("Nikhil Gupta", "nikhil.gupta@logiqbox.in", "mixed", "Logistics SaaS"),
    ("Pooja Desai", "pooja.desai@ahmedabad.craft", "strong", "Craft marketplace"),
    ("Farhan Ali", "farhan.ali@cityrides.in", "weak", "Wallet failures"),
    ("Shreya Kulkarni", "shreya.k@puneapps.in", "strong", "Product studio"),
    ("Manish Agarwal", "manish.a@eastline.in", "mixed", "Wholesale invoices"),
    ("Diya Sen", "diya.sen@kolkata.media", "strong", "Media retainers"),
    ("Rahul Nanda", "rahul.nanda@finstack.in", "strong", "Fintech tool user"),
    ("Aisha Khan", "aisha.khan@lucknow.bazaar", "weak", "First-time high ticket fail"),
    ("Karthik Subramanian", "karthik.s@madras.cloud", "strong", "Cloud credits"),
    ("Nandini Rao", "nandini.rao@hyder.foods", "mixed", "Inventory software"),
    ("Siddharth Jain", "sid.jain@jaipur.stone", "strong", "Export invoices"),
    ("Ritika Malhotra", "ritika.m@gurgaon.hr", "strong", "HR SaaS"),
    ("Omar Sheikh", "omar.s@srinagar.tours", "weak", "Seasonal, many abandons"),
    ("Bhavya Shah", "bhavya.shah@surat.silk", "strong", "Wholesale silk"),
    ("Yashwant Pillai", "yash.pillai@kochi.ports", "mixed", "Freight software"),
    ("Chitra Iyer", "chitra.iyer@madurai.mills", "strong", "Textile ERP"),
    ("Zoya Merchant", "zoya.m@mumbai.atelier", "strong", "Fashion house"),
    ("Pranav Bhatt", "pranav.bhatt@vadodara.chem", "mixed", "Lab supplies"),
    ("Leela Abraham", "leela.a@kochi.health", "strong", "Clinic software"),
    ("Gaurav Tiwari", "gaurav.t@kanpur.yarn", "weak", "Netbanking timeouts"),
    ("Mira Das", "mira.das@guwahati.tea", "strong", "Tea exports"),
    ("Samar Khanna", "samar.k@chandigarh.gym", "mixed", "Gym memberships"),
    ("Anika Bose", "anika.bose@howrah.print", "strong", "Print shop SaaS"),
    ("Rehan Siddiqui", "rehan.s@noida.ads", "weak", "Ad spend card declines"),
    ("Pallavi Joshi", "pallavi.j@indore.learn", "strong", "Edtech"),
    ("Vivek Chauhan", "vivek.c@dehradun.wood", "mixed", "Furniture B2B"),
    ("Sneha Patil", "sneha.patil@nashik.wine", "strong", "DTC wine club"),
    ("Iqbal Hussain", "iqbal.h@patna.logistics", "weak", "Account blocked"),
    ("Keerthi Nair", "keerthi.n@trivandrum.space", "strong", "Incubator dues"),
    ("Aarav Gupta", "aarav.g@ncr.mobility", "mixed", "Fleet software"),
    ("Myra Kapoor", "myra.k@delhi.events", "strong", "Event ticketing"),
    ("Raghav Sinha", "raghav.s@ranchi.mines", "weak", "EMI defaults"),
    ("Tanvi Rao", "tanvi.rao@vizag.ports", "strong", "Port ops SaaS"),
    ("Eshan Dutta", "eshan.d@siliguri.trade", "mixed", "Cross-border"),
    ("Harini Prasad", "harini.p@bengaluru.biotech", "strong", "Lab SaaS"),
    ("Kabir Mehta", "kabir.m@ahmedabad.solar", "strong", "Energy invoices"),
    ("Sana Kapur", "sana.kapur@goa.hospitality", "mixed", "Hotel PMS"),
    ("Devika Rani", "devika.r@mysore.silk", "strong", "Handloom"),
    ("Arnav Bose", "arnav.bose@durgapur.steel", "weak", "Do not honor"),
    ("Nisha Varghese", "nisha.v@kochi.media", "strong", "Production house"),
    ("Varun Sethi", "varun.sethi@ludhiana.auto", "mixed", "Spare parts"),
    ("Aditi Kulkarni", "aditi.k@kolhapur.learn", "strong", "Coaching"),
    ("Mohit Yadav", "mohit.y@gwalior.agri", "weak", "Insufficient funds"),
    ("Rhea D'Souza", "rhea.d@mangalore.fish", "strong", "Export docs"),
    ("Kunal Bansal", "kunal.b@faridabad.parts", "mixed", "Auto-retry candidate"),
]


def _stable_int(text: str, modulo: int) -> int:
    digest = sha256(text.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % modulo


def seed_database(db: Session, force: bool = False) -> dict:
    existing = db.query(Customer).count()
    if existing and not force:
        return {"seeded": False, "customers": existing}

    if force:
        db.query(AgentAction).delete()
        db.query(PaymentLink).delete()
        db.query(RecoveryOpportunity).delete()
        db.query(Transaction).delete()
        db.query(Customer).delete()
        db.commit()

    now = utcnow()
    customers: list[Customer] = []
    for idx, (name, email, profile, _note) in enumerate(CUSTOMER_SEEDS, start=1):
        customer = Customer(
            external_customer_id=f"cust_{idx:03d}",
            name=name,
            email=email,
            phone=f"+9198{_stable_int(email, 10000000):07d}"[:13],
        )
        db.add(customer)
        customers.append(customer)
    db.flush()

    tx_id = 1
    for customer, (_name, _email, profile, _note) in zip(customers, CUSTOMER_SEEDS):
        cid = customer.id
        if profile == "strong":
            captured_n, fail_n = 8, 1
        elif profile == "mixed":
            captured_n, fail_n = 5, 2
        else:
            captured_n, fail_n = 1, 3

        for i in range(captured_n):
            amount = AMOUNTS[(cid + i) % (len(AMOUNTS) - 2)]
            method = METHODS[(cid + i) % 3]
            db.add(
                Transaction(
                    external_transaction_id=f"txn_{tx_id:04d}",
                    customer_id=cid,
                    amount=amount,
                    currency="INR",
                    status="captured",
                    payment_method=method,
                    failure_reason=None,
                    created_at=now - timedelta(days=70 - i * 6, hours=cid % 12),
                    recovered=False,
                )
            )
            tx_id += 1

        fail_plan = []
        if profile == "strong":
            fail_plan = [
                (24999 if cid % 2 == 0 else 12999, "bank_timeout", "upi", 2),
            ]
            if cid % 5 == 0:
                fail_plan.append((8499, "abandoned", "card", 6))
        elif profile == "mixed":
            fail_plan = [
                (4999, "insufficient_funds", "card", 4),
                (1999, "network_error", "upi", 9),
            ]
            if cid % 3 == 0:
                fail_plan.append((49999, "issuer_unavailable", "netbanking", 1))
        else:
            fail_plan = [
                (8499, "card_expired", "card", 5),
                (12999, "account_blocked", "netbanking", 8),
                (999, "abandoned", "wallet", 12),
            ]
            if cid % 4 == 0:
                fail_plan.append((24999, "do_not_honor", "emi", 3))

        for amount, reason, method, days_ago in fail_plan:
            status = "abandoned" if reason == "abandoned" else "failed"
            db.add(
                Transaction(
                    external_transaction_id=f"txn_{tx_id:04d}",
                    customer_id=cid,
                    amount=amount,
                    currency="INR",
                    status=status,
                    payment_method=method,
                    failure_reason=reason,
                    created_at=now - timedelta(days=days_ago, hours=cid % 8),
                    recovered=False,
                )
            )
            tx_id += 1

        if cid % 7 == 0:
            db.add(
                Transaction(
                    external_transaction_id=f"txn_{tx_id:04d}",
                    customer_id=cid,
                    amount=1999,
                    currency="INR",
                    status="refunded",
                    payment_method="upi",
                    failure_reason=None,
                    created_at=now - timedelta(days=20),
                    recovered=False,
                )
            )
            tx_id += 1

    db.commit()

    for customer in db.query(Customer).all():
        refresh_customer_stats(db, customer)
    db.commit()

    created_opps = rebuild_opportunities(db)

    tx_count = db.query(Transaction).count()
    db.add(
        AgentAction(
            opportunity_id=None,
            agent_name="Revenue Agent",
            action="analyse_ledger",
            decision="completed",
            risk_level="low",
            reason=f"Analysed {tx_count} transactions.",
            created_at=now,
        )
    )
    db.add(
        AgentAction(
            opportunity_id=None,
            agent_name="Recovery Agent",
            action="identify_opportunities",
            decision="completed",
            risk_level="low",
            reason=f"Identified {created_opps} recovery opportunities.",
            created_at=now,
        )
    )
    db.add(
        AgentAction(
            opportunity_id=None,
            agent_name="Recovery Agent",
            action="generate_recommendations",
            decision="completed",
            risk_level="low",
            reason=f"Generated {created_opps} structured recovery recommendations.",
            created_at=now,
        )
    )
    db.commit()
    return {
        "seeded": True,
        "customers": db.query(Customer).count(),
        "transactions": tx_count,
        "opportunities": created_opps,
    }
