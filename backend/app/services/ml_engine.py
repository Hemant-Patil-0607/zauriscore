import logging
from typing import Dict

logger = logging.getLogger(__name__)


class MLRiskEngine:
    """
    CodeBERT-based ML risk scoring engine.
    Generates embeddings from contract source and predicts vulnerability probability.
    """

    MODEL_NAME = "microsoft/codebert-base"
    MAX_LENGTH = 512

    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._classifier = None
        self._loaded = False

    def _load_model(self):
        """Lazy-loads the model on first use."""
        if self._loaded:
            return

        try:
            import torch
            from transformers import AutoTokenizer, AutoModel
            import numpy as np

            self._tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)
            self._model = AutoModel.from_pretrained(self.MODEL_NAME)
            self._model.eval()
            self._torch = torch
            self._np = np
            self._loaded = True
            logger.info("CodeBERT model loaded successfully")
        except ImportError:
            logger.warning("PyTorch/Transformers not available — using fallback ML scoring")
            self._loaded = True  # Mark loaded to avoid retrying

    def analyze(self, source_code: str) -> Dict:
        """
        Returns ML risk probability (0.0 to 1.0) and score (0-100).
        Falls back to heuristic-based estimate if model unavailable.
        """
        self._load_model()

        if self._model is None:
            return self._fallback_score(source_code)

        try:
            return self._run_inference(source_code)
        except Exception as e:
            logger.error(f"ML inference error: {e}")
            return self._fallback_score(source_code)

    def _run_inference(self, source_code: str) -> Dict:
        """Runs CodeBERT embedding + risk classification."""
        import torch

        # Truncate to max token length
        truncated = source_code[:4000]

        inputs = self._tokenizer(
            truncated,
            return_tensors="pt",
            max_length=self.MAX_LENGTH,
            truncation=True,
            padding=True,
        )

        with torch.no_grad():
            outputs = self._model(**inputs)

        # Use CLS token embedding as contract representation
        cls_embedding = outputs.last_hidden_state[:, 0, :]  # (1, 768)
        embedding_norm = cls_embedding.norm().item()

        # Heuristic classifier on embedding norm
        # A proper deployment would use a fine-tuned classification head here
        # trained on labeled vulnerable/safe contracts
        raw_probability = self._embedding_to_risk(cls_embedding, source_code)

        score = round(raw_probability * 100, 2)

        return {
            "ml_probability": raw_probability,
            "score": score,
            "model": self.MODEL_NAME,
            "method": "codebert_embedding",
        }

    def _embedding_to_risk(self, embedding, source_code: str) -> float:
        """
        Maps CodeBERT CLS embedding to risk probability.
        This uses a simple linear projection as a placeholder for a
        fine-tuned classifier head. Replace with trained weights in production.
        """
        import torch

        # Compute basic risk signals from embedding statistics
        e = embedding.squeeze()
        mean_val = e.mean().item()
        std_val = e.std().item()

        # Supplement with source-based signals
        source_signals = self._source_risk_signals(source_code)

        # Combine embedding statistics with source signals
        raw = (abs(mean_val) * 0.3 + std_val * 0.2 + source_signals * 0.5)
        probability = min(1.0, max(0.0, raw / 2.0))

        return probability

    def _source_risk_signals(self, source_code: str) -> float:
        """Quick pattern-based risk signal for ML augmentation."""
        import re
        high_risk_patterns = [
            r"\bselfdestruct\b",
            r"\.delegatecall\s*\(",
            r"\btx\.origin\b",
            r"\bassembly\s*\{",
        ]
        signal = 0.0
        for pattern in high_risk_patterns:
            if re.search(pattern, source_code, re.IGNORECASE):
                signal += 0.25
        return min(1.0, signal)

    def _fallback_score(self, source_code: str) -> Dict:
        """Fallback scoring when PyTorch is unavailable."""
        signal = self._source_risk_signals(source_code)
        score = round(signal * 100, 2)
        return {
            "ml_probability": signal,
            "score": score,
            "model": "fallback",
            "method": "pattern_based",
        }


ml_risk_engine = MLRiskEngine()
