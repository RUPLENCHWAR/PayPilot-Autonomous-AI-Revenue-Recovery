import hashlib
import hmac
from typing import Optional


def verify_razorpay_signature(body: bytes, signature: Optional[str], secret: str) -> bool:
    if not signature or not secret:
        return False
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, signature)


def unique_reference(prefix: str, opportunity_id: int) -> str:
    return f"{prefix}_{opportunity_id}_{int(__import__('time').time())}"
