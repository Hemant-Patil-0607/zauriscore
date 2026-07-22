from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User, Scan, Contract, ScanStatus
from app.schemas.schemas import ScanCreate, ScanStatusResponse, ScanReportOut, ScanListItem
from app.services.rate_limiter import rate_limiter
from app.workers.tasks import run_scan

router = APIRouter(prefix="/scan", tags=["scans"])


@router.post("", response_model=ScanStatusResponse, status_code=status.HTTP_202_ACCEPTED)
def create_scan(
    body: ScanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check rate limit
    allowed, used, limit = rate_limiter.check_and_consume(
        str(current_user.id), current_user.plan.value
    )
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Used {used}/{limit} scans today. Upgrade your plan for more scans.",
        )

    # Get or create contract record
    contract = (
        db.query(Contract)
        .filter(Contract.address == body.address, Contract.chain_id == body.chain_id)
        .first()
    )
    if not contract:
        contract = Contract(
            address=body.address,
            chain_id=body.chain_id,
        )
        db.add(contract)
        db.flush()

    # Create scan job
    scan = Scan(
        user_id=current_user.id,
        contract_id=contract.id,
        status=ScanStatus.queued,
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    # Dispatch to worker queue
    try:
        run_scan.apply_async(args=[str(scan.id)], queue="scans")
    except Exception as e:
        # Enqueue failed: mark scan as failed, refund quota, return error
        scan.status = ScanStatus.failed
        scan.error_message = f"Enqueue failed: {str(e)}"
        db.commit()
        rate_limiter.refund(str(current_user.id), current_user.plan.value)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Scan queue is unavailable. Please try again later.",
        )

    return scan


@router.get("/{scan_id}", response_model=ScanReportOut)
def get_scan(
    scan_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scan = (
        db.query(Scan)
        .filter(Scan.id == scan_id, Scan.user_id == current_user.id)
        .first()
    )
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@router.get("", response_model=List[ScanListItem])
def list_scans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0,
):
    scans = (
        db.query(Scan, Contract)
        .join(Contract, Scan.contract_id == Contract.id)
        .filter(Scan.user_id == current_user.id)
        .order_by(Scan.created_at.desc())
        .offset(offset)
        .limit(min(limit, 100))
        .all()
    )

    result = []
    for scan, contract in scans:
        result.append(
            ScanListItem(
                id=scan.id,
                address=contract.address,
                chain_id=contract.chain_id,
                status=scan.status.value,
                risk_score=scan.risk_score,
                decision=scan.decision.value if scan.decision else None,
                created_at=scan.created_at,
            )
        )
    return result
