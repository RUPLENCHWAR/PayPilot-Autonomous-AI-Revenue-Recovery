# PayPilot — Autonomous AI Revenue Recovery

> **Turn failed payments into recoverable revenue — intelligently, safely, and autonomously.**

PayPilot is an AI-powered revenue recovery system built for the **Razorpay AI Builder Internship 2026 — Track 3: AI Revenue Recovery**.

Instead of blindly retrying every failed payment, PayPilot analyzes transaction context and customer behavior, estimates recovery probability and expected value, chooses the most suitable recovery strategy, and executes the action within merchant-defined safety boundaries.

---

## 🚀 The Problem

A failed payment does not necessarily mean lost revenue.

Different failures require different interventions:

- Temporary failures may benefit from a retry.
- Customers with strong payment history may be better suited for a payment link.
- Some customers may need a reminder.
- High-value or risky transactions may require human approval.
- Some failures should simply receive no further action.

Traditional recovery systems often rely on fixed retry rules.

**PayPilot makes recovery an intelligent decision.**

---

## 💡 Our Solution

PayPilot creates an autonomous recovery loop:

```text
Failed Payment
      ↓
Revenue Intelligence
      ↓
Customer Intelligence
      ↓
Recovery Probability
      ↓
Expected Recovery / ROI
      ↓
AI Recovery Strategist
      ↓
RecoveryGuard
      ↓
Razorpay
      ↓
Payment Event / Webhook
      ↓
Recovered Revenue
      ↓
Revenue Analytics

The goal is not to maximize the number of retries.

The goal is to maximize valuable recovered revenue while minimizing unnecessary actions and risk.

🤖 AI Recovery Decision

For every recovery opportunity, PayPilot evaluates:

Transaction amount
Failure reason
Customer payment history
Successful payments
Failed payments
Customer lifetime value
Previous recovery attempts
Recovery probability
Expected recovery
Risk level
Merchant autonomy policy

The system then selects a recovery strategy such as:

Silent Retry
Payment Link
Reminder
Payment Method Change
Human Review
No Action

The AI also explains:

Why this customer?
Why recover?
Why this strategy?
Why not the alternatives?
🧠 Hybrid AI Architecture

PayPilot intentionally does not give an LLM unrestricted control over financial actions.

                    ┌─────────────────────┐
                    │   Payment Signals   │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Revenue Intelligence│
                    │ Deterministic Logic  │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Recovery Probability│
                    │ Expected Value / ROI │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ AI Recovery         │
                    │ Strategist           │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │   RecoveryGuard      │
                    │ Policy Enforcement   │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │      Razorpay        │
                    └──────────┬──────────┘
                               ↓
                         Payment Event
                               ↓
                    ┌─────────────────────┐
                    │ Revenue Ledger      │
                    └─────────────────────┘
Deterministic layer

Responsible for:

Financial calculations
Recovery probability
Expected recovery
ROI
Amount limits
Duplicate prevention
State validation
Safety policies
AI layer

Responsible for:

Recovery strategy selection
Contextual reasoning
Alternative comparison
Explanations
Customer-facing messaging
Natural-language analysis

This separation ensures that the LLM can recommend, but cannot bypass financial safety controls.

🛡️ RecoveryGuard

RecoveryGuard is the safety layer between AI decisions and financial execution.

Merchants can define:

Autonomous Recovery: ON/OFF

Maximum Autonomous Amount: ₹10,000

Allowed:
✓ Payment Link
✓ Retry
✓ Reminder

Restricted:
⚠ High-value actions
⚠ High-risk actions
✕ Refunds

If an opportunity exceeds the merchant's configured autonomy limit, PayPilot automatically escalates it for human approval.

This creates:

AI autonomy + merchant control + financial guardrails

📊 Expected Recovery & ROI

PayPilot distinguishes between:

Revenue at Risk

Total value of failed payments.

Expected Recovery

Estimated recoverable amount based on recovery probability.

Expected Recovery =
Transaction Amount × Recovery Probability
Expected Net Recovery
Expected Net Recovery =
Expected Recovery − Estimated Recovery Cost
Recovery ROI
Recovery ROI =
Expected Net Recovery / Estimated Recovery Cost

Recovery cost is configurable/demo-based and is clearly presented as an estimate rather than an actual operational cost.

🔍 Recovery Simulator

The Recovery Simulator allows merchants to understand the effect of different autonomy policies.

A merchant can change the autonomous recovery limit and immediately see:

Autonomous opportunities
Human approval opportunities
Expected recovery
Additional expected recovery unlocked

This turns autonomy from a fixed setting into a measurable business decision.

🧩 Agent Trace

Every recovery workflow can be followed through an agent trace:

Revenue Agent
     ↓
Customer Intelligence
     ↓
Recovery Agent
     ↓
Recovery Strategist
     ↓
RecoveryGuard
     ↓
Razorpay Agent
     ↓
Webhook
     ↓
Revenue Ledger

The trace provides visibility into:

Agent
Decision
Status
Timestamp
Reason
Risk level

This creates an auditable recovery workflow rather than a black-box AI decision.

💳 Razorpay Integration

PayPilot is designed to work with:

Demo Mode

A safe environment for demonstrating the complete workflow without real financial transactions.

Razorpay Test Mode

Uses Razorpay's test environment for payment-link and payment-event workflows.

The application keeps financial credentials strictly on the backend.

Production payments are not enabled by default.

🔄 Recovery Flow

Example:

₹12,999 payment fails
        ↓
PayPilot detects revenue at risk
        ↓
Customer history analyzed
        ↓
Recovery probability = 88%
        ↓
Expected recovery calculated
        ↓
AI compares strategies
        ↓
Payment Link selected
        ↓
RecoveryGuard checks policy
        ↓
Action approved
        ↓
Razorpay payment link created
        ↓
Customer completes payment
        ↓
Webhook received
        ↓
Payment verified
        ↓
Revenue ledger updated
        ↓
₹12,999 recovered

The system closes the loop from payment failure → decision → execution → measurable recovery.

🔐 Reliability & Safety

PayPilot includes safeguards for:

Duplicate recovery prevention
Recovered-state protection
Unique payment references
Webhook idempotency
Webhook signature verification
Autonomous amount limits
High-risk action restrictions
Human approval escalation
Backend-only financial credentials
AI fallback when an LLM API is unavailable

A payment event cannot simply be counted multiple times because the same webhook was received repeatedly.

🏗️ Project Structure
paypilot/
│
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   ├── api/
│   │   ├── services/
│   │   ├── models.py
│   │   └── main.py
│   │
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── package.json
│   └── .env.example
│
├── docs/
│   ├── architecture.md
│   └── demo-script.md
│
├── .gitignore
└── README.md
⚙️ Tech Stack
Frontend
Next.js
React
TypeScript
Tailwind CSS
Recharts
Backend
Python
FastAPI
SQLAlchemy
Pydantic
AI
OpenAI-compatible LLM integration
Deterministic fallback strategy engine
Payments
Razorpay APIs
Razorpay Test Mode
Webhooks
Database
SQLite for local/demo development
SQLAlchemy ORM
🛠️ Local Setup
1. Clone the repository
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd paypilot
2. Backend
cd backend

python -m venv venv

Windows:

venv\Scripts\activate

Install dependencies:

pip install -r requirements.txt

Create your environment file:

backend/.env

using:

backend/.env.example

Start the backend:

uvicorn app.main:app --reload

Backend:

http://127.0.0.1:8000

API documentation:

http://127.0.0.1:8000/docs
3. Frontend

Open another terminal:

cd frontend
npm install
npm run dev

Frontend:

http://localhost:3000

Dashboard:

http://localhost:3000/dashboard
