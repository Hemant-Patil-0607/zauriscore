from typing import Dict


class DecisionEngine:
    """
    Calculates the final deterministic risk score and GO/REVIEW/NO-GO decision.

    Formula:
        risk_score = 0.5 * static_analysis_score
                   + 0.3 * heuristic_score
                   + 0.2 * ml_score

    Thresholds:
        0–40   → GO
        40–70  → REVIEW
        70–100 → NO-GO
    """

    WEIGHTS = {
        "static": 0.5,
        "heuristic": 0.3,
        "ml": 0.2,
    }

    THRESHOLDS = {
        "GO": (0, 40),
        "REVIEW": (40, 70),
        "NO-GO": (70, 100),
    }

    def calculate(
        self,
        static_score: float,
        heuristic_score: float,
        ml_score: float,
    ) -> Dict:
        """Returns risk_score, decision, and confidence."""

        risk_score = round(
            self.WEIGHTS["static"] * static_score
            + self.WEIGHTS["heuristic"] * heuristic_score
            + self.WEIGHTS["ml"] * ml_score,
            2,
        )

        decision = self._get_decision(risk_score)
        confidence = self._calculate_confidence(static_score, heuristic_score, ml_score)

        return {
            "risk_score": risk_score,
            "decision": decision,
            "confidence": confidence,
            "static_score": round(static_score, 2),
            "heuristic_score": round(heuristic_score, 2),
            "ml_score": round(ml_score, 2),
        }

    def _get_decision(self, score: float) -> str:
        for decision, (low, high) in self.THRESHOLDS.items():
            if low <= score < high:
                return decision
        return "NO-GO"  # default for score == 100

    def _calculate_confidence(
        self,
        static_score: float,
        heuristic_score: float,
        ml_score: float,
    ) -> float:
        """
        Confidence reflects agreement between scoring components.
        High agreement = high confidence.
        """
        scores = [static_score, heuristic_score, ml_score]
        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        std_dev = variance ** 0.5

        # Lower std dev → higher confidence
        confidence = max(50.0, min(99.0, 99.0 - std_dev * 0.8))
        return round(confidence, 1)


decision_engine = DecisionEngine()
