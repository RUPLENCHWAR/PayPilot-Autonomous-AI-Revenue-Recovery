# PayPilot 5-minute demo

Do not quote invented recovery totals. Read the numbers on the dashboard after the backend has seeded.

## 0:00–0:30 — Problem

Indian merchants using Razorpay still leak revenue after a charge fails or a customer drops off checkout. Finance teams export CSVs. Success rates go on a slide. Nobody owns the next action, and nobody can say how much cash actually came back.

## 0:30–1:00 — PayPilot introduction

PayPilot is an autonomous recovery desk. It does not replace Razorpay. It sits on top of the payment ledger, decides a recovery action, runs RecoveryGuard, and either creates a Payment Link or asks a human.

Open [http://localhost:3000/dashboard](http://localhost:3000/dashboard). Point to **Demo Mode** or **Razorpay Test Mode** in the header so judges know this is not live money.

## 1:00–2:00 — Revenue leakage detection

Show **Revenue at risk** (unpaid recoverable volume) versus **AI recoverable** (probability-weighted expected recovery). Call out **Actual recovered** starting at ₹0 if nothing has been simulated yet.

Click through failed-payment mix and a high-value row. Open a loyal customer (for example Priya Mehta / Neha Sharma) versus a weak-history customer (Arjun Kapoor / Vikram Singh) to show the engine is using history, not a single fail flag.

Optional command bar: `Show me the biggest revenue leaks.`

## 2:00–3:00 — AI recovery reasoning

Open Recovery Center → a high-value failed UPI timeout. Click **Analyze**.

Read the three explanations:

- Why this customer?  
- Why recover?  
- Why this action?

State the source: **Local recovery engine** unless an OpenAI key is configured. Do not claim an LLM ran if the badge says local.

## 3:00–4:00 — RecoveryGuard + Razorpay action

Point at **AUTO APPROVED** on a sub-₹10,000 low-risk case, then a ₹24,999 / ₹49,999 case labelled **HUMAN APPROVAL REQUIRED**.

Click **Recover** or **Approve & execute**.

- Demo: banner “Demo Mode — No real payment was created.”  
- Test keys: a real Razorpay test Payment Link URL. If Razorpay errors, show the error — do not pretend it succeeded.

## 4:00–4:30 — Payment success / recovery

In demo mode click **Simulate Success**. Return to the dashboard: **Actual recovered** should increase by that transaction amount. Agent Activity should show Razorpay Agent + RecoveryGuard rows.

If using Razorpay test mode, complete the test payment and let the webhook mark capture. Do not use simulate endpoints in test mode.

## 4:30–5:00 — Architecture + differentiation

One sentence: ledger → score → agent JSON → RecoveryGuard → Payment Links → webhook/sim → recovered revenue.

Close with:

> We didn't build another payment dashboard. We built an autonomous recovery layer that turns payment signals into recovered revenue.

Stay honest: the scorer is a demo model, this is an MVP, and test/demo payments are not live settlements.
