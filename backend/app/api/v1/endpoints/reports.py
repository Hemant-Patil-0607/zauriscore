from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User, Scan, Vulnerability, Provenance

router = APIRouter(prefix="/report", tags=["reports"])


class VulnOut(BaseModel):
    severity: str
    detector: str
    description: str
    location: Optional[str]
    source: Optional[str]


class ReportOut(BaseModel):
    scan_id: str
    contract_address: str
    chain_id: int
    risk_score: float
    decision: str
    confidence: float
    static_score: float
    heuristic_score: float
    ml_score: float
    vulnerabilities: List[VulnOut]
    solc_version: Optional[str]
    slither_version: Optional[str]
    source_hash: Optional[str]
    block_number: Optional[int]
    analysis_timestamp: Optional[datetime]
    report_json_url: Optional[str]
    report_md_url: Optional[str]
    report_pdf_url: Optional[str]
    completed_at: Optional[datetime]


@router.get("/{scan_id}", response_model=ReportOut)
def get_report(
    scan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scan = (
        db.query(Scan)
        .filter(Scan.id == scan_id, Scan.user_id == current_user.id)
        .first()
    )
    if not scan:
        raise HTTPException(status_code=404, detail="Report not found")

    if scan.status.value != "completed":
        raise HTTPException(
            status_code=400, detail=f"Scan is not completed yet (status: {scan.status.value})"
        )

    prov = db.query(Provenance).filter(Provenance.scan_id == scan.id).first()
    contract = scan.contract
    vulns = (
        db.query(Vulnerability).filter(Vulnerability.scan_id == scan.id).all()
    )

    return ReportOut(
        scan_id=str(scan.id),
        contract_address=contract.address,
        chain_id=contract.chain_id,
        risk_score=scan.risk_score or 0,
        decision=scan.decision.value if scan.decision else "UNKNOWN",
        confidence=scan.confidence or 0,
        static_score=scan.static_score or 0,
        heuristic_score=scan.heuristic_score or 0,
        ml_score=scan.ml_score or 0,
        vulnerabilities=[
            VulnOut(
                severity=v.severity.value,
                detector=v.detector,
                description=v.description,
                location=v.location,
                source=v.source,
            )
            for v in vulns
        ],
        solc_version=prov.solc_version if prov else None,
        slither_version=prov.slither_version if prov else None,
        source_hash=prov.source_hash if prov else None,
        block_number=prov.block_number if prov else None,
        analysis_timestamp=prov.analysis_timestamp if prov else None,
        report_json_url=scan.report_json_url,
        report_md_url=scan.report_md_url,
        report_pdf_url=scan.report_pdf_url,
        completed_at=scan.completed_at,
    )
