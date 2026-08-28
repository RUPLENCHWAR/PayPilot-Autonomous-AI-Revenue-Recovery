from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import SessionLocal, init_db
from app.routes import dashboard, recovery, transactions, webhooks
from app.seed.seed_data import seed_database


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield


settings = get_settings()
app = FastAPI(
    title="PayPilot API",
    description="Autonomous AI revenue recovery agent for Razorpay merchants.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router, prefix="/api")
app.include_router(transactions.router, prefix="/api")
app.include_router(recovery.router, prefix="/api")
app.include_router(webhooks.router, prefix="/api")


@app.get("/")
def root():
    return {
        "name": "PayPilot",
        "docs": "/docs",
        "health": "/api/health",
    }
