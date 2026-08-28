import json
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import WebhookEvent
from app.database import get_db
from app.services.recovery_service import apply_webhook_payment
from app.utils.security import verify_razorpay_signature

router = APIRouter(tags=["webhooks"])


@router.post("/webhooks/razorpay")
async def razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_razorpay_signature: Optional[str] = Header(default=None, alias="X-Razorpay-Signature"),
):
    body = await request.body()
    settings = get_settings()
    if settings.webhook_secret_configured:
        if not verify_razorpay_signature(body, x_razorpay_signature, settings.razorpay_webhook_secret):
            raise HTTPException(401, "Invalid Razorpay webhook signature")
    elif settings.effective_razorpay_mode == "test":
        raise HTTPException(401, "Webhook secret is required in Razorpay test mode")

    try:
        payload = json.loads(body.decode("utf-8") or "{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(400, "Invalid JSON") from exc

    event = payload.get("event", "")
    event_id = request.headers.get("X-Razorpay-Event-Id") or payload.get("id")
    if event_id:
        existing = db.query(WebhookEvent).filter(WebhookEvent.event_id == event_id).first()
        if existing:
            return {"ok": True, "duplicate": True, "event": event}
    entity = (payload.get("payload") or {})
    payment = ((entity.get("payment") or {}).get("entity")) or {}
    order = ((entity.get("order") or {}).get("entity")) or {}
    link = ((entity.get("payment_link") or {}).get("entity")) or {}

    notes = payment.get("notes") or link.get("notes") or {}
    reference_id = link.get("reference_id") or notes.get("reference_id")
    link_id = link.get("id") or notes.get("payment_link_id")
    captured = event in {"payment.captured", "order.paid", "payment_link.paid"}
    failed = event in {"payment.failed", "payment_link.expired"}
    if not captured and not failed:
        return {"ok": True, "ignored": event}

    applied = apply_webhook_payment(
        db,
        reference_id=reference_id,
        link_id=link_id,
        captured=captured,
        amount_paise=payment.get("amount") or link.get("amount"),
    )
    if event_id:
        db.add(WebhookEvent(event_id=event_id, event_type=event))
        db.commit()
    return {"ok": True, "applied": applied, "event": event}
