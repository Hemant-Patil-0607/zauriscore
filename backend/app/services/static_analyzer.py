import subprocess
import json
import os
import tempfile
import shutil
from typing import List, Dict
from app.core.config import settings


class SlitherAnalyzer:
    """Runs Slither static analysis on a smart contract source."""

    # Detectors to run and their severity mapping
    DETECTOR_SEVERITY = {
        "reentrancy-eth": "high",
        "reentrancy-no-eth": "medium",
        "unchecked-lowlevel": "high",
        "unchecked-send": "high",
        "controlled-delegatecall": "high",
        "delegatecall-loop": "medium",
        "tx-origin": "medium",
        "suicidal": "critical",
        "unprotected-upgrade": "critical",
        "arbitrary-send-eth": "critical",
        "arbitrary-send-erc20": "high",
        "controlled-array-length": "high",
        "integer-overflow": "medium",
        "shadowing-state": "medium",
        "msg-value-loop": "medium",
        "weak-prng": "medium",
        "events-access": "low",
        "missing-zero-check": "low",
    }

    def analyze(self, source_code: str, compiler_version: str, contract_name: str) -> Dict:
        """
        Runs Slither on the provided Solidity source.
        Returns dict with findings and aggregate score.
        """
        work_dir = tempfile.mkdtemp(prefix="zauriscore-")
        try:
            return self._run_analysis(work_dir, source_code, compiler_version, contract_name)
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    def _run_analysis(self, work_dir: str, source_code: str, compiler_version: str, contract_name: str) -> Dict:
        # Write contract to temp file
        contract_file = os.path.join(work_dir, "Contract.sol")
        with open(contract_file, "w") as f:
            f.write(source_code)

        # Select correct solc version
        self._select_solc_version(compiler_version)

        # Run Slither
        cmd = [
            "slither",
            contract_file,
            "--json",
            "-",
            "--disable-color",
            "--timeout",
            str(settings.slither_timeout),
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=settings.slither_timeout + 10,
                cwd=work_dir,
            )
        except subprocess.TimeoutExpired:
            return self._empty_result("Slither analysis timed out")
        except FileNotFoundError:
            return self._empty_result("Slither not installed")

        # Slither returns exit code 1 when vulnerabilities are found — that's expected
        slither_output = result.stdout

        if not slither_output:
            return self._empty_result("No output from Slither")

        try:
            data = json.loads(slither_output)
        except json.JSONDecodeError:
            return self._empty_result("Failed to parse Slither output")

        findings = self._parse_findings(data)
        score = self._calculate_score(findings)

        # Get slither version for provenance
        try:
            ver_result = subprocess.run(
                ["slither", "--version"], capture_output=True, text=True, timeout=5
            )
            slither_version = ver_result.stdout.strip()
        except Exception:
            slither_version = "unknown"

        return {
            "findings": findings,
            "score": score,
            "slither_version": slither_version,
            "raw_detectors_count": len(findings),
        }

    def _parse_findings(self, data: dict) -> List[Dict]:
        findings = []
        detectors = data.get("results", {}).get("detectors", [])

        for det in detectors:
            check = det.get("check", "unknown")
            impact = det.get("impact", "Informational").lower()
            description = det.get("description", "")

            # Extract location from first element
            elements = det.get("elements", [])
            location = ""
            if elements:
                elem = elements[0]
                src = elem.get("source_mapping", {})
                filename = elem.get("name", "")
                lines = src.get("lines", [])
                if lines:
                    location = f"{filename}:{lines[0]}"

            severity = self.DETECTOR_SEVERITY.get(check, impact)

            findings.append({
                "detector": check,
                "severity": severity,
                "description": description.strip(),
                "location": location,
                "source": "slither",
            })

        return findings

    def _calculate_score(self, findings: List[Dict]) -> float:
        """Converts findings into a 0-100 risk score component."""
        weights = {
            "critical": 25,
            "high": 15,
            "medium": 8,
            "low": 3,
            "informational": 1,
        }
        total = sum(weights.get(f["severity"], 1) for f in findings)
        # Normalize: cap at 100
        return min(100.0, total)

    def _select_solc_version(self, compiler_version: str):
        """Attempts to select the correct solc version."""
        if not compiler_version:
            return
        # Normalize: strip commit hash
        ver = compiler_version.split("+")[0].lstrip("v")
        try:
            subprocess.run(
                ["solc-select", "install", ver],
                capture_output=True,
                timeout=60,
            )
            subprocess.run(
                ["solc-select", "use", ver],
                capture_output=True,
                timeout=10,
            )
        except Exception:
            pass  # Continue with default solc

    def _empty_result(self, reason: str) -> Dict:
        return {
            "findings": [],
            "score": 0.0,
            "slither_version": "unknown",
            "raw_detectors_count": 0,
            "error": reason,
        }


slither_analyzer = SlitherAnalyzer()
