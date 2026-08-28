from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    razorpay_mode: str
    ai_mode: str
    openai_configured: bool
    razorpay_configured: bool


class DashboardMetrics(BaseModel):
    total_revenue: float
    revenue_at_risk: float
    recoverable_revenue: float
    recovered_revenue: float
    recovery_rate: float
    recovery_confidence: float
    opportunity_count: int
    pending_approvals: int
    auto_approved_count: int
    transaction_count: int
    failed_count: int
    customer_count: int
    razorpay_mode: str
    ai_mode: str


class TrendPoint(BaseModel):
    date: str
    captured: float
    failed: float
    recovered: float


class FailureBreakdown(BaseModel):
    reason: str
    count: int
    amount: float


class TopCustomer(BaseModel):
    id: int
    name: str
    email: str
    expected_recovery: float
    failed_amount: float
    recovery_score: float


class DashboardResponse(BaseModel):
    metrics: DashboardMetrics
    trend: list[TrendPoint]
    failure_breakdown: list[FailureBreakdown]
    recent_actions: list["AgentActionOut"]
    top_customers: list[TopCustomer]
    opportunities: list["OpportunityOut"]


class CustomerOut(BaseModel):
    id: int
    external_customer_id: str
    name: str
    email: str
    phone: str
    total_paid: float
    successful_payments: int
    failed_payments: int
    average_transaction_value: float
    lifetime_value: float
    recovery_score: float

    model_config = {"from_attributes": True}


class TransactionOut(BaseModel):
    id: int
    external_transaction_id: str
    customer_id: int
    amount: float
    currency: str
    status: str
    payment_method: str
    failure_reason: Optional[str]
    created_at: datetime
    recovered: bool
    recovery_probability: Optional[float]
    recommended_action: Optional[str]
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None

    model_config = {"from_attributes": True}


class PaymentLinkOut(BaseModel):
    id: int
    opportunity_id: int
    razorpay_link_id: Optional[str]
    short_url: str
    amount: float
    status: str
    created_at: datetime
    reference_id: str
    mode: str

    model_config = {"from_attributes": True}


class AgentActionOut(BaseModel):
    id: int
    opportunity_id: Optional[int]
    agent_name: str
    action: str
    decision: str
    risk_level: str
    reason: str
    created_at: datetime

    model_config = {"from_attributes": True}


class OpportunityOut(BaseModel):
    id: int
    transaction_id: int
    customer_id: int
    amount: float
    recovery_probability: float
    expected_recovery: float
    estimated_recovery_cost: float = 25.0
    expected_net_recovery: float = 0.0
    recovery_roi: float = 0.0
    recovery_strategy: Optional[str] = None
    priority: str
    reason: str
    recommended_action: str
    status: str
    created_at: datetime
    why_customer: Optional[str] = None
    why_recover: Optional[str] = None
    why_action: Optional[str] = None
    risk_level: Optional[str] = None
    customer_message: Optional[str] = None
    ai_source: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    failure_reason: Optional[str] = None
    payment_method: Optional[str] = None
    transaction_status: Optional[str] = None

    model_config = {"from_attributes": True}


class GuardDecision(BaseModel):
    allowed: bool
    requires_approval: bool
    auto_approved: bool
    risk_level: str
    reasons: list[str]
    policy_label: str


class RecoveryAnalysis(BaseModel):
    decision: str
    recommended_action: str
    recovery_probability: float
    expected_recovery: float
    estimated_recovery_cost: float = 25.0
    expected_net_recovery: float = 0.0
    recovery_roi: float = 0.0
    recovery_strategy: Optional[str] = None
    risk_level: str
    reason: str
    customer_message: str
    why_customer: str
    why_recover: str
    why_action: str
    ai_source: str
    guard: GuardDecision


class ExecuteResponse(BaseModel):
    ok: bool
    message: str
    requires_approval: bool = False
    auto_approved: bool = False
    opportunity: Optional[OpportunityOut] = None
    payment_link: Optional[PaymentLinkOut] = None
    analysis: Optional[RecoveryAnalysis] = None
    demo_mode: bool = False
    razorpay_mode: str = "demo"


class CommandRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    confirm: bool = False


class CommandResponse(BaseModel):
    intent: str
    title: str
    answer: str
    requires_confirmation: bool = False
    data: dict[str, Any] = Field(default_factory=dict)


class AutonomyUpdate(BaseModel):
    autonomous_amount_limit: int = Field(ge=1000, le=100000)
    enabled: bool = True


class SettingsOut(BaseModel):
    razorpay_mode: str
    razorpay_configured: bool
    ai_mode: str
    openai_configured: bool
    autonomous_amount_limit: int
    webhook_configured: bool
    frontend_url: str


DashboardResponse.model_rebuild()
