# PayPilot

Autonomous AI revenue recovery agent that turns failed and abandoned Razorpay payments into structured recovery actions — then executes them safely.

## Problem

Merchants lose revenue after a payment fails, a checkout is abandoned, or a recurring charge declines. Most payment dashboards stop at reporting. They show that money was lost. They do not decide what to do next, they do not enforce a safety policy, and they do not close the loop back to recovered cash.

## Solution

PayPilot is an operations layer on top of Razorpay:

1. Ingest transaction and customer history  
2. Score recoverable leakage with a transparent demo model  
3. Generate a structured recovery decision (local engine or OpenAI)  
4. Validate the decision with **RecoveryGuard**  
5. Create a Razorpay Payment Link (test) or a labelled demo link  
6. Record webhooks or demo simulations  
7. Update actual recovered revenue — never a hardcoded KPI

## Why a payment dashboard is not enough

A dashboard can tell you *what failed*. PayPilot answers *whether it is recoverable*, *which action to take*, *whether a human must approve*, and *whether the money actually came back*.

## How it works

Transaction data → Revenue intelligence → AI recovery decision → RecoveryGuard → Razorpay action → payment status → recovered revenue.

## Architecture

See [docs/architecture.md](docs/architecture.md).

## AI agents

- **Revenue Agent** scores leakage from ledger features.  
- **Recovery Agent** recommends `retry`, `payment_link`, `reminder`, `manual_review`, or `no_action`.  
- **RecoveryGuard** blocks duplicates, refunds, over-limit amounts, and high-risk actions.  
- **Razorpay Agent** creates payment links or records demo links.

If `OPENAI_API_KEY` is missing, recommendations still run on the **local recovery engine**. The UI labels the source honestly.

## RecoveryGuard

- Amounts ≤ ₹10,000 and low risk may auto-execute.  
- Amounts > ₹10,000 require human approval.  
- High-risk actions always require approval.  
- Refunds never execute autonomously.

## Razorpay integration

Official API: `POST https://api.razorpay.com/v1/payment_links`  
Amounts are sent in paise. Secrets stay on the backend.

| `RAZORPAY_MODE` | Credentials | Behaviour |
| --- | --- | --- |
| `demo` (default) | optional | Labelled demo link, no Razorpay call |
| `test` | key id + secret required | Real Razorpay Test API. Failures are shown, never faked. |

Webhook: `POST /api/webhooks/razorpay` verifies `X-Razorpay-Signature` when a webhook secret is configured.

## Tech stack

- Frontend: Next.js (App Router), TypeScript, Tailwind CSS, Recharts  
- Backend: FastAPI, Pydantic, SQLAlchemy, SQLite  
- AI: OpenAI optional, deterministic fallback  
- Payments: Razorpay Payment Links (test) or demo mode  

This is a hackathon MVP, not production-ready software.

## Setup (Windows PowerShell)

Open **two terminals**. One for the API, one for the UI.

### Backend (terminal 1)

```powershell
cd C:\Users\ASUS\Desktop\paypilot\backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

The API seeds a deterministic SQLite ledger on first start.

- Backend: [http://localhost:8000](http://localhost:8000)  
- OpenAPI: [http://localhost:8000/docs](http://localhost:8000/docs)

### Frontend (terminal 2)

```powershell
cd C:\Users\ASUS\Desktop\paypilot\frontend
copy .env.example .env.local
npm install
npm run dev
```

- Frontend: [http://localhost:3000](http://localhost:3000)

## Environment variables

Copy `backend/.env.example` to `backend/.env` (do not commit `.env`).

```
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=
OPENAI_API_KEY=
RAZORPAY_MODE=demo
AI_MODE=local
DATABASE_URL=sqlite:///./paypilot.db
FRONTEND_URL=http://localhost:3000
AUTONOMOUS_AMOUNT_LIMIT=10000
```

Frontend: `NEXT_PUBLIC_API_URL=http://localhost:8000`

Leave Razorpay and OpenAI keys empty for a full local demo.

To use Razorpay Test Mode, put **test** keys in `.env` and set `RAZORPAY_MODE=test`. Never use live keys for this project. Test payments are not real settlements.

To use OpenAI, set `OPENAI_API_KEY` and `AI_MODE=openai`. Otherwise the local engine is used.

## Demo mode

The header shows **Demo Mode** when no live Razorpay test call is made. After Recover, open the opportunity and use **Simulate Success** / **Simulate Failure**. That path is blocked when Razorpay test mode is on — real captures must arrive via webhook.

## Testing

```powershell
cd C:\Users\ASUS\Desktop\paypilot\backend
.\venv\Scripts\Activate.ps1
pytest
```

## API surface

- `GET /api/dashboard`  
- `GET /api/transactions`  
- `GET /api/recovery/opportunities`  
- `GET /api/customers`  
- `GET /api/agent/activity`  
- `POST /api/recovery/{id}/analyze`  
- `POST /api/recovery/{id}/execute`  
- `POST /api/recovery/{id}/approve`  
- `POST /api/recovery/{id}/simulate-success`  
- `POST /api/recovery/{id}/simulate-failure`  
- `POST /api/webhooks/razorpay`  
- `POST /api/command`

## Project structure

```
backend/app/          FastAPI, agents, services, seed
backend/tests/        scoring, guard, recovery, API tests
frontend/app/         Next.js pages
docs/                 architecture + 5-minute demo script
```

## Screenshots

Add screenshots here after a local run:

- Dashboard hero (revenue at risk vs AI recoverable)  
- Recovery Center card with RecoveryGuard label  
- Agent activity timeline  
- Demo payment simulation  

## Future improvements

- PostgreSQL in production  
- Recurring mandate retries  
- Merchant auth and audit roles  
- Richer webhook coverage  
- Calibrated recovery models (this repo uses a **demo** scorer)

## Limitations

- Not production-ready.  
- Recovery probability is a transparent heuristic, not a validated credit model.  
- Demo simulation is not a Razorpay settlement.  
- No merchant authentication layer.  
- SQLite is for local development only.
