from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_customer_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(160), index=True)
    phone: Mapped[str] = mapped_column(String(32), default="")
    total_paid: Mapped[float] = mapped_column(Float, default=0)
    successful_payments: Mapped[int] = mapped_column(Integer, default=0)
    failed_payments: Mapped[int] = mapped_column(Integer, default=0)
    average_transaction_value: Mapped[float] = mapped_column(Float, default=0)
    lifetime_value: Mapped[float] = mapped_column(Float, default=0)
    recovery_score: Mapped[float] = mapped_column(Float, default=0)

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="customer")
    opportunities: Mapped[list["RecoveryOpportunity"]] = relationship(back_populates="customer")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_transaction_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    status: Mapped[str] = mapped_column(String(32), index=True)
    payment_method: Mapped[str] = mapped_column(String(32))
    failure_reason: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    recovered: Mapped[bool] = mapped_column(Boolean, default=False)
    recovery_probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recommended_action: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    customer: Mapped[Customer] = relationship(back_populates="transactions")
    opportunities: Mapped[list["RecoveryOpportunity"]] = relationship(back_populates="transaction")


class RecoveryOpportunity(Base):
    __tablename__ = "recovery_opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"), index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    amount: Mapped[float] = mapped_column(Float)
    recovery_probability: Mapped[float] = mapped_column(Float)
    expected_recovery: Mapped[float] = mapped_column(Float)
    priority: Mapped[str] = mapped_column(String(16), index=True)
    reason: Mapped[str] = mapped_column(Text)
    recommended_action: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    why_customer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    why_recover: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    why_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    risk_level: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    customer_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_source: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    estimated_recovery_cost: Mapped[float] = mapped_column(Float, default=25.0)
    expected_net_recovery: Mapped[float] = mapped_column(Float, default=0.0)
    recovery_roi: Mapped[float] = mapped_column(Float, default=0.0)
    recovery_strategy: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)

    transaction: Mapped[Transaction] = relationship(back_populates="opportunities")
    customer: Mapped[Customer] = relationship(back_populates="opportunities")
    actions: Mapped[list["AgentAction"]] = relationship(back_populates="opportunity")
    payment_links: Mapped[list["PaymentLink"]] = relationship(back_populates="opportunity")


class AgentAction(Base):
    __tablename__ = "agent_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[Optional[int]] = mapped_column(ForeignKey("recovery_opportunities.id"), nullable=True, index=True)
    agent_name: Mapped[str] = mapped_column(String(64), index=True)
    action: Mapped[str] = mapped_column(String(64))
    decision: Mapped[str] = mapped_column(String(64))
    risk_level: Mapped[str] = mapped_column(String(16), default="low")
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    opportunity: Mapped[Optional[RecoveryOpportunity]] = relationship(back_populates="actions")


class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(64))
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RecoveryCampaign(Base):
    __tablename__ = "recovery_campaigns"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(32), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PaymentLink(Base):
    __tablename__ = "payment_links"
    __table_args__ = (UniqueConstraint("reference_id", name="uq_payment_link_reference"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("recovery_opportunities.id"), index=True)
    razorpay_link_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    short_url: Mapped[str] = mapped_column(String(255))
    amount: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(32), default="created")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reference_id: Mapped[str] = mapped_column(String(64), unique=True)
    mode: Mapped[str] = mapped_column(String(16), default="demo")

    opportunity: Mapped[RecoveryOpportunity] = relationship(back_populates="payment_links")
