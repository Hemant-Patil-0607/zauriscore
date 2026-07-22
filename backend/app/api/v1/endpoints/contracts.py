from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User, Contract, Scan

router = APIRouter(prefix="/contract", tags=["contracts"])


class ContractScanSummary(BaseModel):
    scan_id: str
    status: str
    risk_score: Optional[float]
    decision: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ContractDetail(BaseModel):
    id: str
    address: str
    chain_id: int
    name: Optional[str]
    verified: bool
    compiler_version: Optional[str]
    source_hash: Optional[str]
    scan_count: int
    latest_risk_score: Optional[float]
    latest_decision: Optional[str]
    scans: List[ContractScanSummary]

    class Config:
        from_attributes = True


@router.get("/{address}", response_model=ContractDetail)
def get_contract(
    address: str,
    chain_id: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    address = address.strip().lower()
    contract = (
        db.query(Contract)
        .filter(Contract.address == address, Contract.chain_id == chain_id)
        .first()
    )
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    scans = (
        db.query(Scan)
        .filter(Scan.contract_id == contract.id, Scan.user_id == current_user.id)
        .order_by(Scan.created_at.desc())
        .limit(10)
        .all()
    )

    latest = scans[0] if scans else None

    return ContractDetail(
        id=str(contract.id),
        address=contract.address,
        chain_id=contract.chain_id,
        name=contract.name,
        verified=contract.verified,
        compiler_version=contract.compiler_version,
        source_hash=contract.source_hash,
        scan_count=len(scans),
        latest_risk_score=latest.risk_score if latest else None,
        latest_decision=latest.decision.value if latest and latest.decision else None,
        scans=[
            ContractScanSummary(
                scan_id=str(s.id),
                status=s.status.value,
                risk_score=s.risk_score,
                decision=s.decision.value if s.decision else None,
                created_at=s.created_at,
            )
            for s in scans
        ],
    )
