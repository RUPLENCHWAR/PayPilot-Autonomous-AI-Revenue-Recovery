from pathlib import Path
from functools import lru_cache

_runtime_autonomous_limit: int | None = None
_runtime_autonomous_enabled: bool = True

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///./paypilot.db"
    frontend_url: str = "http://localhost:3000"
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""
    razorpay_mode: str = "demo"
    openai_api_key: str = ""
    ai_mode: str = "local"
    autonomous_amount_limit: int = 10000

    @property
    def razorpay_configured(self) -> bool:
        return bool(self.razorpay_key_id and self.razorpay_key_secret)

    @property
    def effective_autonomous_amount_limit(self) -> int:
        return _runtime_autonomous_limit if _runtime_autonomous_limit is not None else self.autonomous_amount_limit

    @property
    def autonomous_enabled(self) -> bool:
        return _runtime_autonomous_enabled

    @property
    def effective_razorpay_mode(self) -> str:
        mode = (self.razorpay_mode or "demo").lower().strip()
        if mode == "test" and self.razorpay_configured:
            return "test"
        return "demo"

    @property
    def openai_configured(self) -> bool:
        return bool(self.openai_api_key) and self.ai_mode.lower() != "local"

    @property
    def webhook_secret_configured(self) -> bool:
        return bool(self.razorpay_webhook_secret)


@lru_cache
def get_settings() -> Settings:
    return Settings()


def update_autonomy_settings(limit: int | None = None, enabled: bool | None = None) -> None:
    global _runtime_autonomous_limit, _runtime_autonomous_enabled
    if limit is not None:
        _runtime_autonomous_limit = int(limit)
    if enabled is not None:
        _runtime_autonomous_enabled = bool(enabled)
