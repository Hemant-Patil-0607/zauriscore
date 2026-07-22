import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime,
    ForeignKey, Text, Enum, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


def utcnow():
    return datetime.now(timezone.utc)


class PlanTier(str, enum.Enum):
    free = "free"
    pro = "pro"
    enterprise = "enterprise"


class ScanStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class Decision(str, enum.Enum):
    go = "GO"
    review = "REVIEW"
    no_go = "NO-GO"


class Severity(str, enum.Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    informational = "informational"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    plan = Column(Enum(PlanTier), default=PlanTier.free, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    scans = relationship("Scan", back_populates="user")
    subscription = relationship("BillingSubscription", back_populates="user", uselist=False)


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    address = Column(String(42), nullable=False)
    chain_id = Column(Integer, nullable=False)
    name = Column(String(255))
    source_hash = Column(String(66))
    verified = Column(Boolean, default=False)
    compiler_version = Column(String(50))
    created_at = Column(DateTime(timezone=True), default=utcnow)

    scans = relationship("Scan", back_populates="contract")

    __table_args__ = (
        Index("ix_contracts_address_chain", "address", "chain_id", unique=True),
    )


class Scan(Base):
    __tablename__ = "scans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id"), nullable=False)
    status = Column(Enum(ScanStatus), default=ScanStatus.queued, nullable=False)
    risk_score = Column(Float)
    decision = Column(Enum(Decision))
    confidence = Column(Float)
    static_score = Column(Float)
    heuristic_score = Column(Float)
    ml_score = Column(Float)
    error_message = Column(Text)
    report_json_url = Column(String(512))
    report_md_url = Column(String(512))
    report_pdf_url = Column(String(512))
    created_at = Column(DateTime(timezone=True), default=utcnow, index=True)
    completed_at = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="scans")
    contract = relationship("Contract", back_populates="scans")
    vulnerabilities = relationship("Vulnerability", back_populates="scan", cascade="all, delete-orphan")
    provenance = relationship("Provenance", back_populates="scan", uselist=False, cascade="all, delete-orphan")
    risk_score_record = relationship("RiskScore", back_populates="scan", uselist=False, cascade="all, delete-orphan")


class Vulnerability(Base):
    __tablename__ = "vulnerabilities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id = Column(UUID(as_uuid=True), ForeignKey("scans.id"), nullable=False, index=True)
    severity = Column(Enum(Severity), nullable=False)
    detector = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String(512))
    source = Column(String(50))  # slither | heuristic | ml

    scan = relationship("Scan", back_populates="vulnerabilities")


class Provenance(Base):
    __tablename__ = "provenance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id = Column(UUID(as_uuid=True), ForeignKey("scans.id"), nullable=False, unique=True)
    contract_address = Column(String(42), nullable=False)
    chain_id = Column(Integer, nullable=False)
    block_number = Column(Integer)
    source_hash = Column(String(66))
    solc_version = Column(String(50))
    slither_version = Column(String(50))
    analysis_timestamp = Column(DateTime(timezone=True), default=utcnow)

    scan = relationship("Scan", back_populates="provenance")


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id = Column(UUID(as_uuid=True), ForeignKey("scans.id"), nullable=False, unique=True)
    total_score = Column(Float, nullable=False)
    static_analysis_score = Column(Float, nullable=False)
    heuristic_score = Column(Float, nullable=False)
    ml_score = Column(Float, nullable=False)
    decision = Column(Enum(Decision), nullable=False)
    confidence = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    scan = relationship("Scan", back_populates="risk_score_record")


class BillingSubscription(Base):
    __tablename__ = "billing_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    stripe_customer_id = Column(String(255), unique=True)
    stripe_subscription_id = Column(String(255), unique=True)
    plan = Column(Enum(PlanTier), default=PlanTier.free, nullable=False)
    status = Column(String(50), default="active")
    current_period_end = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="subscription")
