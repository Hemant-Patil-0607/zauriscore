import asyncio
import logging
from datetime import datetime, timezone
from celery import shared_task
from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.models import Scan, Contract, Vulnerability, Provenance, RiskScore, ScanStatus, Decision, Severity
from app.services.source_retriever import source_retriever, ContractNotVerifiedError
from app.services.static_analyzer import slither_analyzer
from app.services.heuristics_engine import heuristics_engine
from app.services.ml_engine import ml_risk_engine
from app.services.decision_engine import decision_engine
from app.services.report_generator import report_generator

logger = logging.getLogger(__name__)


def _severity_enum(s: str) -> Severity:
    mapping = {
        "critical": Severity.critical,
        "high": Severity.high,
        "medium": Severity.medium,
        "low": Severity.low,
        "informational": Severity.informational,
    }
    return mapping.get(s.lower(), Severity.informational)


@celery_app.task(bind=True, name="app.workers.tasks.run_scan", max_retries=2, default_retry_delay=30)
def run_scan(self, scan_id: str):
    """
    Full analysis pipeline for a single scan.
    Runs synchronously in Celery worker.
    """
    db = SessionLocal()
    scan = None

    try:
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            logger.error(f"Scan {scan_id} not found")
            return

        contract = scan.contract

        # Mark as running
        scan.status = ScanStatus.running
        db.commit()

        logger.info(f"[{scan_id}] Starting scan for {contract.address} on chain {contract.chain_id}")

        # Stage 1: Source Retrieval
        logger.info(f"[{scan_id}] Stage 1: Retrieving source")
        source_data = asyncio.run(
            source_retriever.fetch_source(contract.address, contract.chain_id)
        )

        source_code = source_data["source_code"]
        compiler_version = source_data["compiler_version"]
        contract_name = source_data["contract_name"]
        block_number = source_data["block_number"]
        source_hash = source_data["source_hash"]

        # Update contract metadata
        contract.compiler_version = compiler_version
        contract.source_hash = source_hash
        contract.verified = True
        db.commit()

        # Stage 2: Static Analysis (Slither)
        logger.info(f"[{scan_id}] Stage 2: Running Slither analysis")
        static_result = slither_analyzer.analyze(source_code, compiler_version, contract_name)

        # Stage 3: Heuristics Engine
        logger.info(f"[{scan_id}] Stage 3: Running heuristics engine")
        heuristic_result = heuristics_engine.analyze(source_code)

        # Stage 4: ML Risk Engine
        logger.info(f"[{scan_id}] Stage 4: Running ML risk engine")
        ml_result = ml_risk_engine.analyze(source_code)

        # Stage 5: Decision Engine
        logger.info(f"[{scan_id}] Stage 5: Calculating risk score and decision")
        decision_result = decision_engine.calculate(
            static_score=static_result["score"],
            heuristic_score=heuristic_result["score"],
            ml_score=ml_result["score"],
        )

        # Save vulnerabilities
        all_findings = (
            static_result.get("findings", [])
            + heuristic_result.get("findings", [])
        )

        for finding in all_findings:
            vuln = Vulnerability(
                scan_id=scan.id,
                severity=_severity_enum(finding.get("severity", "informational")),
                detector=finding.get("detector", "unknown"),
                description=finding.get("description", ""),
                location=finding.get("location", ""),
                source=finding.get("source", "unknown"),
            )
            db.add(vuln)

        # Save provenance
        prov = Provenance(
            scan_id=scan.id,
            contract_address=contract.address,
            chain_id=contract.chain_id,
            block_number=block_number,
            source_hash=source_hash,
            solc_version=compiler_version,
            slither_version=static_result.get("slither_version", "unknown"),
            analysis_timestamp=datetime.now(timezone.utc),
        )
        db.add(prov)

        # Save risk score record
        decision_str = decision_result["decision"]
        decision_enum = {"GO": Decision.go, "REVIEW": Decision.review, "NO-GO": Decision.no_go}.get(decision_str, Decision.review)

        rs = RiskScore(
            scan_id=scan.id,
            total_score=decision_result["risk_score"],
            static_analysis_score=decision_result["static_score"],
            heuristic_score=decision_result["heuristic_score"],
            ml_score=decision_result["ml_score"],
            decision=decision_enum,
            confidence=decision_result["confidence"],
        )
        db.add(rs)
        db.flush()

        # Stage 6: Report Generation
        logger.info(f"[{scan_id}] Stage 6: Generating reports")
        report_data = {
            "scan_id": str(scan.id),
            "contract_address": contract.address,
            "chain_id": contract.chain_id,
            "risk_score": decision_result["risk_score"],
            "decision": decision_str,
            "confidence": decision_result["confidence"],
            "static_score": decision_result["static_score"],
            "heuristic_score": decision_result["heuristic_score"],
            "ml_score": decision_result["ml_score"],
            "vulnerabilities": all_findings,
            "provenance": {
                "solc_version": compiler_version,
                "slither_version": static_result.get("slither_version", "unknown"),
                "source_hash": source_hash,
                "block_number": block_number,
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }

        try:
            report_urls = report_generator.generate_all(str(scan.id), report_data)
            scan.report_json_url = report_urls["json_url"]
            scan.report_md_url = report_urls["md_url"]
            scan.report_pdf_url = report_urls["pdf_url"]
        except Exception as report_err:
            logger.warning(f"[{scan_id}] Report generation failed: {report_err}")

        # Update scan with results
        scan.status = ScanStatus.completed
        scan.risk_score = decision_result["risk_score"]
        scan.decision = decision_enum
        scan.confidence = decision_result["confidence"]
        scan.static_score = decision_result["static_score"]
        scan.heuristic_score = decision_result["heuristic_score"]
        scan.ml_score = decision_result["ml_score"]
        scan.completed_at = datetime.now(timezone.utc)

        db.commit()
        logger.info(f"[{scan_id}] Scan completed. Score: {decision_result['risk_score']}, Decision: {decision_str}")

    except ContractNotVerifiedError as e:
        logger.warning(f"[{scan_id}] Contract not verified: {e}")
        if scan:
            scan.status = ScanStatus.failed
            scan.error_message = f"Contract not verified: {str(e)}"
            db.commit()

    except Exception as e:
        logger.exception(f"[{scan_id}] Scan failed with error: {e}")
        if scan:
            scan.status = ScanStatus.failed
            scan.error_message = str(e)[:500]
            db.commit()
        raise self.retry(exc=e)

    finally:
        db.close()
