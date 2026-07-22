from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum


# ---------------------------------------------------------------------------
# Auth Schemas
# ---------------------------------------------------------------------------

class UserRegister(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    plan: str


class UserOut(BaseModel):
    id: UUID
    email: str
    plan: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Scan Schemas
# ---------------------------------------------------------------------------

class ScanCreate(BaseModel):
    address: str
    chain_id: int = 1  # default ethereum mainnet

    @field_validator("address")
    @classmethod
    def validate_address(cls, v: str) -> str:
        v = v.strip().lower()
        if not v.startswith("0x") or len(v) != 42:
            raise ValueError("Invalid Ethereum address format")
        return v

    @field_validator("chain_id")
    @classmethod
    def validate_chain(cls, v: int) -> int:
        supported = [1, 137, 42161, 8453]  # eth, polygon, arbitrum, base
        if v not in supported:
            raise ValueError(f"Chain {v} not supported. Supported: {supported}")
        return v


class ScanStatusResponse(BaseModel):
    id: UUID
    status: str
    risk_score: Optional[float] = None
    decision: Optional[str] = None
    confidence: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VulnerabilityOut(BaseModel):
    id: UUID
    severity: str
    detector: str
    description: str
    location: Optional[str] = None
    source: Optional[str] = None

    class Config:
        from_attributes = True


class ProvenanceOut(BaseModel):
    contract_address: str
    chain_id: int
    block_number: Optional[int] = None
    source_hash: Optional[str] = None
    solc_version: Optional[str] = None
    slither_version: Optional[str] = None
    analysis_timestamp: datetime

    class Config:
        from_attributes = True


class ScanReportOut(BaseModel):
    id: UUID
    status: str
    risk_score: Optional[float] = None
    decision: Optional[str] = None
    confidence: Optional[float] = None
    static_score: Optional[float] = None
    heuristic_score: Optional[float] = None
    ml_score: Optional[float] = None
    vulnerabilities: List[VulnerabilityOut] = []
    provenance: Optional[ProvenanceOut] = None
    report_json_url: Optional[str] = None
    report_md_url: Optional[str] = None
    report_pdf_url: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScanListItem(BaseModel):
    id: UUID
    address: str
    chain_id: int
    status: str
    risk_score: Optional[float] = None
    decision: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Billing Schemas
# ---------------------------------------------------------------------------

class CheckoutSessionCreate(BaseModel):
    plan: str  # pro | enterprise


class CheckoutSessionResponse(BaseModel):
    checkout_url: str


class SubscriptionOut(BaseModel):
    plan: str
    status: str
    current_period_end: Optional[datetime] = None

    class Config:
        from_attributes = True
