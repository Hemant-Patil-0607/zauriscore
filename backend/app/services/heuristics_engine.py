import re
from typing import List, Dict


class HeuristicsEngine:
    """
    Pattern-based heuristic analysis on Solidity source code.
    Detects admin privilege patterns, mint functions, upgradeable proxies, etc.
    """

    CHECKS = [
        {
            "id": "admin_can_mint",
            "description": "Contract has an unrestricted mint function that could inflate token supply",
            "pattern": r"\bfunction\s+mint\s*\(",
            "severity": "high",
            "weight": 20,
        },
        {
            "id": "owner_withdraw",
            "description": "Owner can withdraw all ETH/tokens from contract",
            "pattern": r"\bfunction\s+withdraw\b.*\bonlyOwner\b|\bonlyOwner\b.*\bwithdraw\b",
            "severity": "medium",
            "weight": 15,
        },
        {
            "id": "upgradeable_proxy",
            "description": "Contract uses upgradeable proxy pattern — logic can be replaced",
            "pattern": r"(UUPSUpgradeable|TransparentUpgradeableProxy|ProxyAdmin|_upgradeTo|upgradeTo)",
            "severity": "medium",
            "weight": 10,
        },
        {
            "id": "selfdestruct_present",
            "description": "Contract contains selfdestruct — can permanently destroy contract",
            "pattern": r"\bselfdestruct\b|\bsuicide\b",
            "severity": "critical",
            "weight": 30,
        },
        {
            "id": "tx_origin_auth",
            "description": "Contract uses tx.origin for authentication — vulnerable to phishing",
            "pattern": r"\btx\.origin\b",
            "severity": "high",
            "weight": 20,
        },
        {
            "id": "dangerous_delegatecall",
            "description": "Contract uses delegatecall to external addresses",
            "pattern": r"\.delegatecall\s*\(",
            "severity": "critical",
            "weight": 25,
        },
        {
            "id": "unchecked_external_call",
            "description": "External call result not checked",
            "pattern": r"\.(call|send)\s*\{[^}]*\}\s*\([^;]*\)\s*;",
            "severity": "high",
            "weight": 18,
        },
        {
            "id": "hardcoded_address",
            "description": "Hardcoded address detected — may indicate centralization risk",
            "pattern": r"0x[0-9a-fA-F]{40}",
            "severity": "low",
            "weight": 5,
        },
        {
            "id": "pause_function",
            "description": "Contract can be paused by admin — centralization risk",
            "pattern": r"\bfunction\s+pause\s*\(|\bWhenNotPaused\b|\bPausable\b",
            "severity": "low",
            "weight": 5,
        },
        {
            "id": "blacklist_function",
            "description": "Contract contains blacklisting capability",
            "pattern": r"\bblacklist\b|\bblocked\b|\bfrozen\b",
            "severity": "medium",
            "weight": 12,
        },
    ]

    def analyze(self, source_code: str) -> Dict:
        """Returns findings list and aggregate heuristic score."""
        findings = []
        total_weight = 0

        for check in self.CHECKS:
            pattern = re.compile(check["pattern"], re.IGNORECASE | re.DOTALL)
            matches = pattern.findall(source_code)

            if matches:
                # Find line numbers
                line_numbers = self._find_lines(source_code, check["pattern"])
                location = f"lines: {', '.join(str(l) for l in line_numbers[:3])}" if line_numbers else ""

                findings.append({
                    "detector": check["id"],
                    "severity": check["severity"],
                    "description": check["description"],
                    "location": location,
                    "source": "heuristic",
                })
                total_weight += check["weight"]

        score = min(100.0, float(total_weight))

        return {
            "findings": findings,
            "score": score,
            "checks_run": len(self.CHECKS),
            "checks_triggered": len(findings),
        }

    def _find_lines(self, source: str, pattern: str) -> List[int]:
        lines = source.split("\n")
        matched = []
        try:
            compiled = re.compile(pattern, re.IGNORECASE)
            for i, line in enumerate(lines, 1):
                if compiled.search(line):
                    matched.append(i)
        except re.error:
            pass
        return matched


heuristics_engine = HeuristicsEngine()
