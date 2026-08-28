from typing import Optional

import httpx

from app.config import get_settings
from app.utils.calculations import to_paise


RAZORPAY_BASE = "https://api.razorpay.com/v1"


class RazorpayError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


class RazorpayService:
    def mode(self) -> str:
        return get_settings().effective_razorpay_mode

    def create_payment_link(
        self,
        *,
        amount_inr: float,
        reference_id: str,
        description: str,
        customer_name: str,
        customer_email: str,
        customer_phone: str,
        notes: Optional[dict] = None,
    ) -> dict:
        settings = get_settings()
        if settings.effective_razorpay_mode == "demo":
            return {
                "id": f"plink_demo_{reference_id}",
                "short_url": f"https://rzp.io/demo/{reference_id}",
                "status": "created",
                "mode": "demo",
            }

        payload = {
            "amount": to_paise(amount_inr),
            "currency": "INR",
            "accept_partial": False,
            "reference_id": reference_id[:40],
            "description": description[:2048],
            "customer": {
                "name": customer_name,
                "email": customer_email,
                "contact": customer_phone or "+919999999999",
            },
            "notify": {"sms": False, "email": False},
            "reminder_enable": True,
            "notes": notes or {},
        }
        try:
            with httpx.Client(timeout=20.0) as client:
                response = client.post(
                    f"{RAZORPAY_BASE}/payment_links",
                    json=payload,
                    auth=(settings.razorpay_key_id, settings.razorpay_key_secret),
                )
        except httpx.HTTPError as exc:
            raise RazorpayError(f"Razorpay network error: {exc}") from exc

        if response.status_code >= 400:
            detail = response.text
            raise RazorpayError(
                f"Razorpay Payment Links API failed ({response.status_code}): {detail}",
                status_code=response.status_code,
            )
        data = response.json()
        return {
            "id": data.get("id"),
            "short_url": data.get("short_url"),
            "status": data.get("status", "created"),
            "mode": "test",
            "raw": data,
        }


razorpay_service = RazorpayService()
