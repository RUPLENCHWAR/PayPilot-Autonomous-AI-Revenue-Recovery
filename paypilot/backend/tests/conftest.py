import os

os.environ.setdefault("RAZORPAY_MODE", "demo")
os.environ.setdefault("AI_MODE", "local")
os.environ.setdefault("DATABASE_URL", "sqlite:///./paypilot_test.db")
os.environ.setdefault("OPENAI_API_KEY", "")
os.environ.setdefault("RAZORPAY_KEY_ID", "")
os.environ.setdefault("RAZORPAY_KEY_SECRET", "")
